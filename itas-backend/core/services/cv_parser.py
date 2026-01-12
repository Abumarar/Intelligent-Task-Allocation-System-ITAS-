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

    @staticmethod
    def extract_details(text: str) -> dict:
        """
        Extract basic details (Name, Role/Title) from CV text.
        This is a heuristic implementation using spaCy.
        """
        import spacy
        import re
        
        details = {
            "name": None,
            "role": None
        }
        
        try:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(text)
            
            # 1. Extract Name (Person)
            # Strategy: First PERSON entity found in the first 500 characters
            # that is distinct from common headers
            first_chunk = text[:1000]
            chunk_doc = nlp(first_chunk)
            
            for ent in chunk_doc.ents:
                if ent.label_ == "PERSON":
                    clean_name = ent.text.strip().title()
                    # Basic filter: 2+ words, no weird symbols
                    if len(clean_name.split()) >= 2 and re.match(r"^[A-Za-z\s\.\-]+$", clean_name):
                        details["name"] = clean_name
                        break
            
            # 2. Extract Role
            # Strategy: Look for common job titles
            roles_db = [
                "Software Engineer", "Java Developer", "Python Developer", "Full Stack Developer",
                "Frontend Developer", "Backend Developer", "DevOps Engineer", "Data Scientist",
                "Project Manager", "Business Analyst", "Product Manager", "QA Engineer",
                "UI/UX Designer", "Scrum Master", "System Administrator", "Database Administrator"
            ]
            
            # Regex for flexibility (e.g., "Senior Java Developer")
            for role in roles_db:
                pattern = re.compile(rf"\b({role})\b", re.IGNORECASE)
                match = pattern.search(first_chunk)
                if match:
                    # Capture the full line/phrase if possible, but for now just the matched role
                    # Or try to capture "Senior" prefix
                    start, end = match.span()
                    # Look back for "Senior", "Lead", "Junior"
                    prefix_match = re.search(r"\b(Senior|Sr\.|Junior|Jr\.|Lead|Principal|Chief)\s+$", first_chunk[:start], re.IGNORECASE)
                    if prefix_match:
                        details["role"] = f"{prefix_match.group(1)} {match.group(1)}".title()
                    else:
                        details["role"] = match.group(1).title()
                    break
                    
        except ImportError:
            print("spaCy not installed or model not found. Skipping detailed extraction.")
        except Exception as e:
            print(f"Error extracting details: {e}")
            
        return details
