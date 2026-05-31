import json

class DatasetNormalizer:
    def __init__(self):
        pass

    def normalize_resume(self, record):
        """
        Standardizes resume record to schema:
        {
          "resume_id": "",
          "raw_text": "",
          "skills": [],
          "education": [],
          "experience_years": 0,
          "domain": ""
        }
        """
        normalized = {
            "resume_id": record.get("resume_id", record.get("id", "")),
            "raw_text": record.get("raw_text", record.get("text", "")),
            "skills": record.get("skills", []),
            "education": record.get("education", []),
            "experience_years": record.get("experience_years", 0),
            "domain": record.get("domain", record.get("category", "")),
        }
        
        if isinstance(normalized["skills"], str):
            try:
                normalized["skills"] = json.loads(normalized["skills"])
            except:
                normalized["skills"] = [s.strip() for s in normalized["skills"].split(",") if s.strip()]
                
        return normalized

    def normalize_task(self, record):
        normalized = {
            "task_id": record.get("task_id", ""),
            "title": record.get("title", ""),
            "description": record.get("description", ""),
            "required_skills": record.get("required_skills", []),
            "priority": record.get("priority", "MEDIUM")
        }
        return normalized
