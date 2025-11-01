"""
Document Ingestion Module
=========================
This module handles uploading and extracting text from policy documents.
Supports: PDF, Word (.docx), and scanned documents (with OCR).
"""

import os
from typing import List, Dict, Optional
import fitz  # PyMuPDF
from docx import Document
import pytesseract
from PIL import Image
import io


class DocumentIngester:
    """
    Handles extraction of text from various document formats.
    Each method is clearly explained for easy understanding.
    """
    
    def __init__(self, use_ocr: bool = True):
        """
        Initialize the document ingester.
        
        Args:
            use_ocr: If True, uses OCR for scanned PDFs when text extraction fails
        """
        self.use_ocr = use_ocr
    
    def extract_from_pdf(self, file_path: str) -> Dict[str, any]:
        """
        Extract text from a PDF file.
        
        Process:
        1. Open PDF using PyMuPDF
        2. Extract text from each page
        3. If text is empty (scanned image), try OCR
        4. Return text with metadata
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with 'text', 'pages', 'file_name', 'total_pages'
        """
        # Open the PDF document
        pdf_document = fitz.open(file_path)
        
        # Get file name for reference
        file_name = os.path.basename(file_path)
        
        # List to store text from all pages
        all_text = []
        total_pages = len(pdf_document)
        
        # Extract text from each page
        for page_num in range(total_pages):
            # Get the page object
            page = pdf_document[page_num]
            
            # Try to extract text directly (works for text-based PDFs)
            page_text = page.get_text()
            
            # If no text found and OCR is enabled, try OCR
            if not page_text.strip() and self.use_ocr:
                # Convert page to image for OCR
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes))
                
                # Use pytesseract to extract text from image
                page_text = pytesseract.image_to_string(image)
            
            # Store page text with page number
            all_text.append({
                'page_num': page_num + 1,
                'text': page_text
            })
        
        # Close the PDF
        pdf_document.close()
        
        # Combine all text into one string
        full_text = '\n\n'.join([page['text'] for page in all_text])
        
        # Return structured data
        return {
            'text': full_text,
            'pages': all_text,  # Keep individual pages for chunking with page numbers
            'file_name': file_name,
            'total_pages': total_pages,
            'file_type': 'pdf'
        }
    
    def extract_from_docx(self, file_path: str) -> Dict[str, any]:
        """
        Extract text from a Word document (.docx).
        
        Process:
        1. Open Word document
        2. Extract text from paragraphs
        3. Return structured text with metadata
        
        Args:
            file_path: Path to the .docx file
            
        Returns:
            Dictionary with 'text', 'paragraphs', 'file_name'
        """
        # Open the Word document
        doc = Document(file_path)
        
        # Get file name
        file_name = os.path.basename(file_path)
        
        # Extract all paragraphs
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():  # Only include non-empty paragraphs
                paragraphs.append(para.text)
        
        # Combine paragraphs with double newlines
        full_text = '\n\n'.join(paragraphs)
        
        # Return structured data
        return {
            'text': full_text,
            'paragraphs': paragraphs,  # Keep individual paragraphs for chunking
            'file_name': file_name,
            'file_type': 'docx'
        }
    
    def ingest_document(self, file_path: str) -> Dict[str, any]:
        """
        Main method to ingest any supported document type.
        Automatically detects file type and calls appropriate extractor.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        # Get file extension to determine type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Route to appropriate extractor
        if file_ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif file_ext == '.docx':
            return self.extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: .pdf, .docx")
    
    def ingest_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, any]]:
        """
        Process multiple documents at once.
        Useful when uploading multiple policy files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of extracted document dictionaries
        """
        results = []
        
        # Process each file
        for file_path in file_paths:
            try:
                # Extract text from document
                extracted = self.ingest_document(file_path)
                results.append(extracted)
            except Exception as e:
                # Log error but continue with other files
                print(f"Error processing {file_path}: {str(e)}")
                results.append({
                    'file_name': os.path.basename(file_path),
                    'error': str(e)
                })
        
        return results


# Example usage (for testing)
if __name__ == "__main__":
    # Initialize ingester
    ingester = DocumentIngester(use_ocr=True)
    
    # Example: Process a single PDF
    # result = ingester.ingest_document("sample_policy.pdf")
    # print(f"Extracted {len(result['text'])} characters from {result['file_name']}")
    pass
