import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import base64
from mistralai import Mistral
import tempfile
import shutil
import time
import requests
import mimetypes

# Set the API key
MISTRAL_API_KEY = "Q2YZJHS8slWMZUdGk1hIZAog6scOjEEU"

class PDFToMarkdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Markdown Converter")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self.setup_ui()
        
    def setup_ui(self):
        # File selection frame
        file_frame = tk.Frame(self.root, pady=10)
        file_frame.pack(fill="x")
        
        self.file_label = tk.Label(file_frame, text="No file selected", width=50, anchor="w")
        self.file_label.pack(side="left", padx=10)
        
        browse_button = tk.Button(file_frame, text="Browse PDF", command=self.browse_file)
        browse_button.pack(side="left", padx=5)
        
        self.convert_button = tk.Button(file_frame, text="Convert to Markdown", command=self.convert_pdf)
        self.convert_button.pack(side="left", padx=5)
        
        # Progress frame (initially hidden)
        self.progress_frame = tk.Frame(self.root, pady=10)
        
        self.progress_label = tk.Label(self.progress_frame, text="Processing...", font=("Helvetica", 10))
        self.progress_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", 
                                            length=500, mode="indeterminate")
        self.progress_bar.pack(pady=(0, 5))
        
        self.progress_status = tk.Label(self.progress_frame, text="Initializing...", font=("Helvetica", 9))
        self.progress_status.pack(pady=(0, 5))
        
        self.cancel_button = tk.Button(self.progress_frame, text="Cancel", command=self.cancel_conversion)
        self.cancel_button.pack()
        
        # Markdown output area
        output_frame = tk.Frame(self.root)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD)
        self.output_text.pack(fill="both", expand=True)
        
        # Bottom buttons frame
        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack(fill="x")
        
        copy_button = tk.Button(button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        copy_button.pack(side="right", padx=10)
        
        save_button = tk.Button(button_frame, text="Save Markdown", command=self.save_markdown)
        save_button.pack(side="right", padx=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.pdf_path = None
        self.cancel_requested = False
        self.conversion_thread = None
        
    def browse_file(self):
        filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        
        if file_path:
            self.pdf_path = file_path
            # Display only the filename, not the full path
            self.file_label.config(text=os.path.basename(file_path))
            self.status_var.set(f"Selected: {os.path.basename(file_path)}")
    
    def show_progress_ui(self):
        # Hide main content temporarily
        self.output_text.pack_forget()
        
        # Show progress elements
        self.progress_frame.pack(pady=20)
        self.progress_bar.start(10)  # Start animation
        
        # Disable convert button
        self.convert_button.config(state=tk.DISABLED)
        
    def hide_progress_ui(self):
        # Stop and hide progress elements
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Show main content again
        self.output_text.pack(fill="both", expand=True)
        
        # Enable convert button
        self.convert_button.config(state=tk.NORMAL)
    
    def update_progress(self, message, is_final=False):
        # Update progress status message
        self.progress_status.config(text=message)
        self.status_var.set(message)
        
        # If final message, pulse the progress bar briefly
        if is_final:
            self.progress_bar.config(mode="determinate")
            self.progress_bar.config(value=100)
        
    def cancel_conversion(self):
        # Set cancel flag for the thread to check
        self.cancel_requested = True
        self.update_progress("Cancelling operation...")
        
    def convert_pdf(self):
        if not self.pdf_path:
            messagebox.showerror("Error", "Please select a PDF file first")
            return
        
        self.output_text.delete(1.0, tk.END)
        self.cancel_requested = False
        
        # Show progress UI
        self.show_progress_ui()
        
        # Run conversion in a separate thread to keep UI responsive
        self.conversion_thread = threading.Thread(target=self._process_conversion)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
    
    def encode_pdf_file(self, file_path):
        """Encode a PDF file to base64."""
        with open(file_path, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
            return encoded_string.decode('utf-8')
    
    def create_temp_file_copy(self, file_path):
        """Create a temporary copy of the file with a unique name."""
        temp_dir = tempfile.gettempdir()
        file_name = os.path.basename(file_path)
        temp_file_path = os.path.join(temp_dir, f"mistral_ocr_{int(time.time())}_{file_name}")
        
        # Copy the file
        shutil.copy2(file_path, temp_file_path)
        return temp_file_path
    
    def _process_conversion(self):
        try:
            # Initialize the Mistral client
            self.update_progress("Initializing Mistral AI client...")
            client = Mistral(api_key=MISTRAL_API_KEY)
            
            if self.cancel_requested:
                self.root.after(0, self._handle_conversion_cancelled)
                return
            
            # Process the PDF document using the file upload approach
            self.update_progress("Preparing PDF file...")
            
            try:
                # Step 1: Upload the file to Mistral's API
                self.update_progress("Uploading PDF file...")
                
                with open(self.pdf_path, "rb") as file:
                    uploaded_file = client.files.upload(
                        file={
                            "file_name": os.path.basename(self.pdf_path),
                            "content": file,
                        },
                        purpose="ocr"
                    )
                
                if self.cancel_requested:
                    self.root.after(0, self._handle_conversion_cancelled)
                    return
                
                # Step 2: Get a signed URL for the uploaded file
                self.update_progress("Getting file access URL...")
                signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
                
                if self.cancel_requested:
                    self.root.after(0, self._handle_conversion_cancelled)
                    return
                
                # Step 3: Process the PDF with OCR
                self.update_progress("Processing PDF with OCR (this may take a while)...")
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": signed_url.url
                    }
                )
                
            except Exception as e:
                # Fall back to direct image_url base64 approach
                self.update_progress(f"Trying alternative method (error: {str(e)})...")
                
                # Use image_url with base64 data URI for PDFs
                try:
                    self.update_progress("Converting PDF to base64 data URI...")
                    pdf_base64 = self.encode_pdf_file(self.pdf_path)
                    
                    # For PDF files, we need to use a specific MIME type
                    mime_type = mimetypes.guess_type(self.pdf_path)[0] or "application/pdf"
                    data_uri = f"data:{mime_type};base64,{pdf_base64}"
                    
                    self.update_progress("Processing with image_url and base64 data...")
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={
                            "type": "image_url",
                            "image_url": data_uri
                        }
                    )
                except Exception as inner_e:
                    # Last resort: Try with a direct PDF URL approach
                    self.update_progress("All methods failed, trying direct URL approach...")
                    
                    # We'll use a document_url with a public accessible URL
                    # For demonstration, we'll use a sample PDF URL
                    # In a real application, you would upload the PDF to a temporary storage service
                    
                    # For now, we'll throw an error to guide the user
                    raise Exception(f"Could not process PDF file. Original error: {str(e)}, Secondary error: {str(inner_e)}")
            
            if self.cancel_requested:
                self.root.after(0, self._handle_conversion_cancelled)
                return
            
            # Extract markdown content
            self.update_progress("Processing OCR results...")
            markdown_content = ocr_response.text
            
            # Final success steps
            self.root.after(0, lambda: self._handle_conversion_success(markdown_content))
            
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: self._handle_conversion_error(error_message))
    
    def _handle_conversion_success(self, markdown_content):
        # Update the UI with the result
        self.output_text.insert(tk.END, markdown_content)
        self.update_progress("Conversion complete!", is_final=True)
        
        # Wait a moment to show completion
        self.root.after(1500, self.hide_progress_ui)
    
    def _handle_conversion_error(self, error_message):
        messagebox.showerror("Error", f"Conversion failed: {error_message}")
        self.status_var.set("Error occurred during conversion")
        self.hide_progress_ui()
    
    def _handle_conversion_cancelled(self):
        self.status_var.set("Conversion cancelled")
        self.hide_progress_ui()
    
    def copy_to_clipboard(self):
        markdown_text = self.output_text.get(1.0, tk.END)
        if markdown_text.strip():
            # Use tkinter's clipboard functionality instead of pyperclip
            self.root.clipboard_clear()
            self.root.clipboard_append(markdown_text)
            self.status_var.set("Copied to clipboard!")
        else:
            messagebox.showinfo("Info", "No content to copy")
    
    def save_markdown(self):
        markdown_text = self.output_text.get(1.0, tk.END)
        if not markdown_text.strip():
            messagebox.showinfo("Info", "No content to save")
            return
            
        # Get original PDF filename without extension
        if self.pdf_path:
            default_filename = os.path.splitext(os.path.basename(self.pdf_path))[0] + ".md"
        else:
            default_filename = "document.md"
            
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(markdown_text)
                self.status_var.set(f"Saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFToMarkdownApp(root)
    root.mainloop() 