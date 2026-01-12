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
                    
                    break
                    
        except ImportError:
            print("CV_PARSER_ERROR: spaCy not installed or model not found. Skipping detailed extraction.")
        except Exception as e:
            print(f"CV_PARSER_ERROR: Error extracting details: {e}")
            
        print(f"CV_PARSER_DEBUG: Extracted text length: {len(text)}")
        print(f"CV_PARSER_DEBUG: Extracted details: {details}")
        return details

    @staticmethod
    def extract_task_details(text: str) -> dict:
        """
        Extract task details (Title, Description, Skills, Priority) from document text.
        """
        import re
        
        details = {
            "title": None,
            "description": None,
            "requiredSkills": [],
            "priority": "MEDIUM"  # Default
        }
        
        if not text:
            return details
            
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # 1. Extract Title
        # Strategy: First non-empty line, or look for "Title:"
        for line in lines[:5]:
            if line.lower().startswith("title:"):
                details["title"] = line.split(":", 1)[1].strip()
                break
            if line.lower().startswith("role:") or line.lower().startswith("position:"):
                 details["title"] = line.split(":", 1)[1].strip()
                 break
        
        if not details["title"] and lines:
            # Fallback to first line if it looks like a title (short-ish)
            if len(lines[0]) < 100:
                details["title"] = lines[0]
        
        # 2. Extract Description
        # Strategy: Everything else, or look for "Description:"
        # For simple parsing, we'll just use the whole text as description if not explicitly found
        description_start = 0
        for i, line in enumerate(lines):
            if "description" in line.lower() and len(line) < 30:
                description_start = i + 1
                break
        
        if description_start > 0:
            details["description"] = "\n".join(lines[description_start:])
        else:
            # If no explicit description section, use the whole text (truncated if too long)
            details["description"] = text[:2000] # Limit length
            
        # 3. Extract Priority
        # Strategy: Keywords
        urgent_keywords = ["urgent", "immediate", "critical", "high priority"]
        if any(w in text.lower() for w in urgent_keywords):
            details["priority"] = "HIGH"
            
        # 4. Extract Skills
        # Reuse logic from SkillExtractor via the view, or duplicate basic extraction here?
        # Ideally, we should use SkillExtractor in the view. 
        # But we can do some basic extraction here if needed, 
        # or just let the View handle the Skill extraction using the existing service.
        # Let's let the View handle robust skill extraction.
        
        return details

    @staticmethod
    def predict_role_with_ai(text: str) -> Optional[str]:
        """
        Predict role using the trained AI model.
        """
        import joblib
        import os
        import re
        from django.conf import settings
        
        # Path to model - assume it's in the base dir or relative
        # Ideally, use settings.BASE_DIR, but for now we'll assume cwd or check
        model_path = os.path.join(settings.BASE_DIR, "resume_classifier_model.pkl")
        
        if not os.path.exists(model_path):
            print(f"CV_PARSER_ERROR: Model not found at {model_path}")
            return None
            
        try:
            model = joblib.load(model_path)
            
            # Clean text (same logic as training)
            def clean_text(t):
                if not isinstance(t, str): return ""
                t = re.sub(r'http\S+\s*', ' ', t)
                t = re.sub(r'RT|cc', ' ', t)
                t = re.sub(r'#\S+', '', t)
                t = re.sub(r'@\S+', '  ', t)
                t = re.sub(r'[^\x00-\x7f]', r' ', t)
                t = re.sub(r'\s+', ' ', t).strip()
                return t
                
            cleaned = clean_text(text)
            print(f"CV_PARSER_DEBUG: Model loaded. Predicting for text length {len(cleaned)}")
            
            # Predict
            prediction = model.predict([cleaned])[0]
            print(f"CV_PARSER_DEBUG: Raw prediction: {prediction}")
            
            # Format: 'INFORMATION-TECHNOLOGY' -> 'Information Technology'
            role = prediction.replace("-", " ").title()
            print(f"CV_PARSER_DEBUG: Formatted Role: {role}")
            return role
            
        except Exception as e:
            print(f"CV_PARSER_ERROR: Error predicting role: {e}")
            return None
