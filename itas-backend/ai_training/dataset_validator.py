class DatasetValidator:
    def validate_resume(self, record):
        errors = []
        if not record.get("raw_text"):
            errors.append("Missing raw_text")
        if not record.get("skills") or len(record.get("skills")) == 0:
            errors.append("Skill sparsity: no skills")
            
        return len(errors) == 0, errors

    def validate_task(self, record):
        errors = []
        if not record.get("title"):
            errors.append("Missing title")
        return len(errors) == 0, errors
        
    def validate_dataset(self, df):
        required_cols = ["raw_text", "skills"]
        for col in required_cols:
            if col not in df.columns:
                return False, f"Missing column: {col}"
        return True, ""
