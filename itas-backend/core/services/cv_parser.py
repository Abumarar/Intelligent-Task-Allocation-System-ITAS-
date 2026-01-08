"""
CV Parsing Service using PyPDF2
Extracts text from uploaded PDF CV files.
"""
import PyPDF2
import io
from typing import Optional


class CVParser:
    """Service for parsing CV/Portfolio PDF files."""

    @staticmethod
    def extract_text_from_pdf(file) -> Optional[str]:
        """
        Extract text content from a PDF file.
        
        Args:
            file: Django UploadedFile or file-like object
            
        Returns:
            Extracted text as string, or None if parsing fails
        """
        try:
            # Read the file content
            if hasattr(file, 'read'):
                file_content = file.read()
            else:
                file_content = file
            
            # Create a PDF file reader
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            extracted_text = "\n\n".join(text_parts)
            return extracted_text.strip() if extracted_text else None
            
        except Exception as e:
            print(f"Error parsing PDF: {str(e)}")
            return None

    @staticmethod
    def is_valid_pdf(file) -> bool:
        """Check if the uploaded file is a valid PDF."""
        try:
            if hasattr(file, 'read'):
                file_content = file.read()
                file.seek(0)  # Reset file pointer
            else:
                file_content = file
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            return len(pdf_reader.pages) > 0
        except Exception:
            return False
