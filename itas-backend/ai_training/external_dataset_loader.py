import os
import glob
import pandas as pd
import kagglehub

class ExternalDatasetLoader:
    def __init__(self, output_dir="ai_training/data/raw_external"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.datasets = [
            "palaksood97/resume-dataset",
            "snehaanbhawal/resume-dataset",
            "jithinjagadeesh/resume-dataset"
        ]

    def fetch_all(self):
        all_resumes = []
        for ds in self.datasets:
            print(f"Downloading dataset: {ds}")
            try:
                path = kagglehub.dataset_download(ds)
                resumes = self._process_dataset(ds, path)
                all_resumes.extend(resumes)
            except Exception as e:
                print(f"Failed to load {ds}: {e}")
                
        if not all_resumes:
            print("No resumes loaded. Skipping.")
            return None
            
        df = pd.DataFrame(all_resumes)
        output_path = os.path.join(self.output_dir, "external_resumes.csv")
        df.to_csv(output_path, index=False)
        print(f"Saved {len(df)} external resumes to {output_path}")
        return output_path

    def _process_dataset(self, name, path):
        # We look for CSV files in the downloaded path
        csv_files = glob.glob(os.path.join(path, "**/*.csv"), recursive=True)
        resumes = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                text_col = None
                cat_col = None
                
                lower_cols = [c.lower() for c in df.columns]
                for i, c in enumerate(lower_cols):
                    if "resume_str" in c or "resume_text" in c or "resume" in c or "text" in c:
                        if text_col is None:
                            text_col = df.columns[i]
                    if "category" in c or "label" in c or "role" in c:
                        if cat_col is None:
                            cat_col = df.columns[i]
                
                if text_col:
                    for _, row in df.iterrows():
                        text = str(row[text_col]) if pd.notnull(row[text_col]) else ""
                        if len(text) > 50:
                            cat = str(row[cat_col]) if cat_col and pd.notnull(row[cat_col]) else ""
                            resumes.append({
                                "source": name,
                                "raw_text": text,
                                "domain": cat
                            })
            except Exception as e:
                print(f"Error processing CSV {csv_file}: {e}")
                
        return resumes

if __name__ == "__main__":
    loader = ExternalDatasetLoader()
    loader.fetch_all()
