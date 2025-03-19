#!/usr/bin/env python3
"""
Command-line script to convert a PDF to markdown using the Mistral OCR API.
Usage: python pdf_to_md_cli.py <pdf_file_path> [output_file_path]

If output_file_path is not provided, the markdown will be saved to a file with the same name as the PDF but with .md extension.
"""

import os
import sys
import json
import requests
import time

# Set your Mistral API key here
MISTRAL_API_KEY = "YOUR_MISTRAL_API_KEY"  # Get your key from https://console.mistral.ai/

def print_progress(message):
    """Print progress message with timestamp."""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {message}")

def upload_pdf_file(file_path):
    """Upload a PDF file to Mistral's files API."""
    print_progress("Uploading PDF file...")
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
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
            raise Exception(f"File upload error: {response.status_code} - {response.text}")
        
        return response.json()

def get_file_url(file_id):
    """Get a signed URL for an uploaded file."""
    print_progress("Getting file access URL...")
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"https://api.mistral.ai/v1/files/{file_id}/url",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"File URL error: {response.status_code} - {response.text}")
    
    return response.json().get("url")

def extract_markdown_from_response(response_data):
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

def process_pdf_to_markdown(pdf_path):
    """Process a PDF file and convert it to markdown using Mistral OCR API."""
    try:
        print_progress(f"Processing file: {os.path.basename(pdf_path)}")
        
        # First try the standard approach with file upload + signed URL
        try:
            # Step 1: Upload the PDF file
            upload_response = upload_pdf_file(pdf_path)
            file_id = upload_response.get("id")
            
            # Step 2: Get a signed URL for the uploaded file
            file_url = get_file_url(file_id)
            
            # Step 3: Process the PDF with OCR
            print_progress("Processing PDF with OCR (this may take a while)...")
            
            headers = {
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
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
            
            print_progress("Extracting markdown content...")
            
            # Extract markdown content from the response
            markdown_content = extract_markdown_from_response(response_data)
            
            if not markdown_content or markdown_content.strip() == "":
                raise Exception("No markdown content found in the API response.")
            
        except Exception as e:
            # Try a fallback with direct multipart form upload
            print_progress(f"Trying direct file upload... (error: {str(e)})")
            
            if os.path.getsize(pdf_path) > 5000000:  # 5MB limit
                raise Exception("File too large for direct processing. Try with a smaller PDF.")
            
            # Directly upload the PDF file for OCR processing
            with open(pdf_path, 'rb') as pdf_file:
                files = {
                    'file': (os.path.basename(pdf_path), pdf_file, 'application/pdf')
                }
                
                # Try binary upload directly with multipart/form-data
                ocr_api_url = "https://api.mistral.ai/v1/ocr"
                
                multipart_headers = {
                    "Authorization": f"Bearer {MISTRAL_API_KEY}"
                }
                
                multipart_data = {
                    "model": "mistral-ocr-latest"
                }
                
                print_progress("Uploading and processing file directly...")
                
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
                markdown_content = extract_markdown_from_response(response_data)
                
                if not markdown_content or markdown_content.strip() == "":
                    raise Exception("No markdown content found in the fallback API response.")
        
        return markdown_content
        
    except Exception as e:
        print_progress(f"Error: {str(e)}")
        return None

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_md_cli.py <pdf_file_path> [output_file_path]")
        return 1
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return 1
    
    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # Use the same name as the PDF but with .md extension
        base_name = os.path.splitext(pdf_path)[0]
        output_path = f"{base_name}.md"
    
    print_progress(f"Starting conversion of {os.path.basename(pdf_path)} to markdown")
    
    # Process the PDF
    markdown_content = process_pdf_to_markdown(pdf_path)
    
    if markdown_content:
        # Save the markdown to the output file
        with open(output_path, 'w', encoding='utf-8') as output_file:
            output_file.write(markdown_content)
            
        print_progress(f"Successfully saved markdown to {output_path}")
        return 0
    else:
        print_progress("Failed to convert PDF to markdown")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 