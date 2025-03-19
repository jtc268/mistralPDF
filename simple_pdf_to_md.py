import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import base64
import time
import json
import requests
import mimetypes

# Set the API key - replace with your own key
API_KEY = "YOUR_MISTRAL_API_KEY"  # Get your key from https://console.mistral.ai/

class SimplePDFToMarkdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF to Markdown Converter")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Load saved API key if it exists
        self.api_key = self.load_api_key()
        
        self.setup_ui()
        
    def setup_ui(self):
        # API key frame
        api_frame = tk.Frame(self.root, pady=10)
        api_frame.pack(fill="x")
        
        api_label = tk.Label(api_frame, text="Mistral API Key:", anchor="w")
        api_label.pack(side="left", padx=10)
        
        self.api_entry = tk.Entry(api_frame, width=40, show="•")
        self.api_entry.pack(side="left", padx=5)
        if self.api_key:
            self.api_entry.insert(0, self.api_key)
        
        self.save_api_button = tk.Button(api_frame, text="Save API Key", command=self.save_api_key)
        self.save_api_button.pack(side="left", padx=5)
        
        self.api_saved_label = tk.Label(api_frame, text="", fg="green", font=("Helvetica", 10))
        self.api_saved_label.pack(side="left", padx=5)
        
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
    
    def save_api_key(self):
        """Save the API key to a local file."""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
            
        try:
            config_dir = os.path.expanduser("~/.mistral_pdf")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
            
            with open(config_file, "w") as f:
                json.dump({"api_key": api_key}, f)
            
            self.api_key = api_key
            
            # Visual feedback sequence
            self.save_api_button.config(state=tk.DISABLED)  # Disable button
            self.api_entry.config(state=tk.DISABLED)  # Disable input
            self.api_saved_label.config(text="Saved!")  # Show saved message
            
            # After 1.5 seconds, re-enable everything
            self.root.after(1500, self._reset_api_ui)
            
            self.status_var.set("API key saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
    
    def _reset_api_ui(self):
        """Reset the API key UI elements after save animation."""
        self.api_entry.config(show="•", state=tk.NORMAL)
        self.save_api_button.config(state=tk.NORMAL)
        self.api_saved_label.config(text="")
    
    def load_api_key(self):
        """Load the API key from the local file."""
        try:
            config_file = os.path.expanduser("~/.mistral_pdf/config.json")
            if os.path.exists(config_file):
                with open(config_file) as f:
                    config = json.load(f)
                    return config.get("api_key", "")
        except Exception:
            pass
        return ""
    
    def get_current_api_key(self):
        """Get the current API key from the entry field."""
        return self.api_entry.get().strip() or self.api_key

    def upload_pdf_file(self, file_path):
        """Upload a PDF file to Mistral's files API."""
        self.update_progress("Uploading PDF file...")
        
        api_key = self.get_current_api_key()
        if not api_key:
            raise Exception("Please enter your Mistral API key")
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Create a multipart form-data request
        with open(file_path, 'rb') as file:
            files = {
                'file': (os.path.basename(file_path), file, 'application/pdf')
            }
            data = {'purpose': 'ocr'}
            
            response = requests.post(
                "https://api.mistral.ai/v1/files",
                headers=headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                if response.status_code == 401:
                    raise Exception("Invalid API key")
                raise Exception(f"Upload failed. Please try again.")
            
            return response.json()
    
    def get_file_url(self, file_id):
        """Get a signed URL for an uploaded file."""
        self.update_progress("Getting file access URL...")
        
        api_key = self.get_current_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"https://api.mistral.ai/v1/files/{file_id}/url",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"File URL error: {response.status_code} - {response.text}")
        
        return response.json().get("url")
    
    def extract_markdown_from_response(self, response_data):
        """Extract markdown content from Mistral OCR API response."""
        if not response_data:
            return "No content returned from the API."
            
        # Try to extract content based on the response format
        try:
            # First check if there's a direct 'text' field
            if 'text' in response_data:
                return response_data['text']
                
            # If not, try to extract from the pages array
            if 'pages' in response_data and isinstance(response_data['pages'], list):
                all_markdown = []
                for page in response_data['pages']:
                    if 'markdown' in page:
                        all_markdown.append(page['markdown'])
                
                if all_markdown:
                    return "\n\n".join(all_markdown)
            
            # Dump the entire response for debugging
            return f"Could not extract markdown content. Full response: {json.dumps(response_data, indent=2)}"
            
        except Exception as e:
            return f"Error extracting markdown: {str(e)}\nResponse: {json.dumps(response_data, indent=2)}"
    
    def _process_conversion(self):
        try:
            # Check for API key first
            if not self.get_current_api_key():
                raise Exception("Please enter your Mistral API key")
                
            # Process the PDF document by using Mistral's file upload + OCR flow
            self.update_progress("Preparing PDF file...")
            
            try:
                # Step 1: Upload the PDF file
                upload_response = self.upload_pdf_file(self.pdf_path)
                file_id = upload_response.get("id")
                
                if self.cancel_requested:
                    self.root.after(0, self._handle_conversion_cancelled)
                    return
                
                # Step 2: Get a signed URL for the uploaded file
                file_url = self.get_file_url(file_id)
                
                if self.cancel_requested:
                    self.root.after(0, self._handle_conversion_cancelled)
                    return
                
                # Step 3: Process the PDF with OCR
                self.update_progress("Processing PDF with OCR (this may take a while)...")
                
                headers = {
                    "Authorization": f"Bearer {self.get_current_api_key()}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "document_url",
                        "document_url": file_url
                    }
                }
                
                # Make the OCR API request
                response = requests.post(
                    "https://api.mistral.ai/v1/ocr",
                    headers=headers,
                    json=data
                )
                
                if response.status_code != 200:
                    raise Exception(f"OCR API error: {response.status_code} - {response.text}")
                
                # Parse the response
                response_data = response.json()
                
                # Debug: Log the full response
                self.update_progress("Extracting markdown content...")
                
                # Extract markdown content from the response
                markdown_content = self.extract_markdown_from_response(response_data)
                
                if not markdown_content or markdown_content.strip() == "":
                    raise Exception("No markdown content found in the API response.")
                
            except Exception as e:
                # Try a fallback with multipart form upload
                self.update_progress(f"Trying direct file upload... (error: {str(e)})")
                
                if os.path.getsize(self.pdf_path) > 5000000:  # 5MB limit
                    raise Exception("File too large for direct processing. Try with a smaller PDF.")
                
                # Directly upload the PDF file for OCR processing
                with open(self.pdf_path, 'rb') as pdf_file:
                    files = {
                        'file': (os.path.basename(self.pdf_path), pdf_file, 'application/pdf')
                    }
                    
                    # Try binary upload directly with multipart/form-data
                    ocr_api_url = "https://api.mistral.ai/v1/ocr"
                    
                    multipart_headers = {
                        "Authorization": f"Bearer {self.get_current_api_key()}"
                    }
                    
                    multipart_data = {
                        "model": "mistral-ocr-latest"
                    }
                    
                    self.update_progress("Uploading and processing file directly...")
                    
                    multipart_response = requests.post(
                        ocr_api_url,
                        headers=multipart_headers,
                        files=files,
                        data=multipart_data
                    )
                    
                    if multipart_response.status_code != 200:
                        raise Exception(f"Fallback OCR failed: {multipart_response.status_code} - {multipart_response.text}. The file format may not be supported.")
                    
                    response_data = multipart_response.json()
                    
                    # Extract markdown content from the fallback response
                    markdown_content = self.extract_markdown_from_response(response_data)
                    
                    if not markdown_content or markdown_content.strip() == "":
                        raise Exception("No markdown content found in the fallback API response.")
            
            if self.cancel_requested:
                self.root.after(0, self._handle_conversion_cancelled)
                return
            
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
        # Simplify common error messages
        simplified_error = self._simplify_error_message(error_message)
        messagebox.showerror("Error", simplified_error)
        self.status_var.set("Conversion failed")
        self.hide_progress_ui()
    
    def _simplify_error_message(self, error):
        """Convert technical errors into user-friendly messages."""
        error = str(error).lower()
        
        # API key related errors
        if "unauthorized" in error or "invalid token" in error or "authentication" in error:
            return "Invalid API key. Please check your Mistral API key and try again."
            
        # File related errors
        if "file too large" in error:
            return "PDF file is too large. Please try a smaller file (under 5MB)."
            
        if "file format" in error or "not supported" in error:
            return "Invalid file format. Please ensure you're uploading a valid PDF."
            
        # API response errors
        if "no markdown content" in error:
            return "Could not extract content from the PDF. Please try a different file."
            
        if "ocr api error" in error:
            return "OCR processing failed. Please try again or use a different PDF."
            
        # Network errors
        if "connection" in error or "timeout" in error:
            return "Network error. Please check your internet connection."
            
        # Default case - keep it brief
        return "Conversion failed. Please try again with a different PDF."
    
    def _handle_conversion_cancelled(self):
        self.status_var.set("Conversion cancelled")
        self.hide_progress_ui()
    
    def copy_to_clipboard(self):
        markdown_text = self.output_text.get(1.0, tk.END)
        if markdown_text.strip():
            # Use tkinter's clipboard functionality
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
    app = SimplePDFToMarkdownApp(root)
    root.mainloop() 