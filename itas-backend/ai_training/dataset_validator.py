class DatasetValidator:
    def validate_dataset(self, df):
        required_cols = ["raw_text", "skills"]
        for col in required_cols:
            if col not in df.columns:
                return False, f"Missing column: {col}"
        return True, ""
