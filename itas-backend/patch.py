import os

filepath = r'core\services\cv_parser.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Spacy 1000 to 3 lines
content = content.replace('first_chunk = text[:1000]', 'first_chunk = "\\n".join(text.splitlines()[:3])[:200]')

# 2. Name extraction blocklist replace
old_blocklist = '''                            blocklist = [
                                "Asp.Net", "Asp.Net Core", "React", "Node.Js", "Java", "Python", 
                                "Html", "Css", "Sql", "Git",
                                "Software Engineer", "Full Stack Developer", "Frontend Developer", 
                                "Backend Developer", "DevOps Engineer", "Data Scientist", 
                                "Project Manager", "Business Analyst", "Product Manager", 
                                "QA Engineer", "UI/UX Designer", "Scrum Master", 
                                "System Administrator", "Database Administrator"
                            ]

                            # Ensure it doesn't match email domain or contain @
                            is_valid_name = True
                            if "@" in clean_name:
                                is_valid_name = False
                            elif details["email"] and clean_name.lower().replace(" ", "") in details["email"].lower():
                                is_valid_name = False
                            
                            # Check against blocklist
                            for blocked in blocklist:
                                if blocked.lower() in clean_name.lower():
                                    is_valid_name = False
                                    break'''

new_blocklist = '''                            is_valid_name = True
                            if "@" in clean_name:
                                is_valid_name = False
                            elif details["email"] and clean_name.lower().replace(" ", "") in details["email"].lower():
                                is_valid_name = False

                            # Check against blocklist using substring matching for robust filtering
                            invalid_name_words = {
                                "software", "network", "system", "licensing", "management", 
                                "administration", "technology", "information", "project", "data", 
                                "business", "analyst", "engineer", "developer", "manager", 
                                "server", "database", "admin", "lead", "director", "coordinator",
                                "summary", "professional", "experience", "education", "skills",
                                "certifications", "hardware", "infrastructure", "troubleshooting",
                                "quality", "assurance", "testing", "operations", "vendor"
                            }
                            
                            if is_valid_name:
                                for word in clean_name.lower().split():
                                    if word in invalid_name_words:
                                        is_valid_name = False
                                        break'''

content = content.replace(old_blocklist, new_blocklist)

# 3. LLM Title extraction and match.group bug fix
old_roles = '''            # roles_db scan
            if not details["role"]:
                cleaned_text = _clean_spacing(text[:1000])
                for role in roles_db:
                    pattern = re.compile(re.escape(role), re.IGNORECASE)
                    match = pattern.search(cleaned_text)
                    if match:
                        start, _ = match.span()
                        prefix_match = re.search(
                            r"\\b(Senior|Sr\.|Junior|Jr\.|Lead|Principal|Chief)\\s+$",
                            cleaned_text[:start],
                            re.IGNORECASE,
                        )
                        if prefix_match:
                            details["role"] = f"{prefix_match.group(1)} {match.group(1)}".title()
                        else:
                            details["role"] = match.group(1).title()
                        break'''

new_roles = '''            # Try to extract the title using LLM (Generative AI)
            if not details["role"]:
                llm_title = CVParser.extract_title_with_llm(text)
                if llm_title:
                    details["role"] = llm_title
                    print(f"CV_PARSER_DEBUG: LLM Extracted Role: {llm_title}")

            # roles_db scan
            if not details["role"]:
                cleaned_text = _clean_spacing(text[:1000])
                for role in roles_db:
                    pattern = re.compile(re.escape(role), re.IGNORECASE)
                    match = pattern.search(cleaned_text)
                    if match:
                        start, _ = match.span()
                        prefix_match = re.search(
                            r"\\b(Senior|Sr\.|Junior|Jr\.|Lead|Principal|Chief)\\s+$",
                            cleaned_text[:start],
                            re.IGNORECASE,
                        )
                        if prefix_match:
                            details["role"] = f"{prefix_match.group(1)} {role}".title()
                        else:
                            details["role"] = role.title()
                        break'''

content = content.replace(old_roles, new_roles)

# 4. Add extract_title_with_llm method
llm_method = '''
    @staticmethod
    def extract_title_with_llm(text: str) -> str | None:
        """
        Use Google Gemini to extract the most recent job title from a CV.
        """
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("CV_PARSER_DEBUG: GEMINI_API_KEY not found. Skipping LLM title extraction.")
            return None
            
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            
            prompt = (
                "You are an expert HR assistant. Extract the single most recent job title "
                "of the applicant from the following CV text. "
                "Return ONLY the exact job title as a string, nothing else. "
                "If it's an anonymized CV with no job experience or no clear title, return the word 'NONE'.\\n\\n"
                f"CV Text:\\n{text[:4000]}"
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                ),
            )
            
            result = response.text.strip()
            if result.upper() == 'NONE' or not result:
                return None
                
            return result.title()
        except Exception as e:
            print(f"CV_PARSER_ERROR: LLM Title Extraction failed: {e}")
            return None
'''

if 'def extract_title_with_llm' not in content:
    content += llm_method

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Patch applied successfully.')
