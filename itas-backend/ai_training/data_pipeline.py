import os
import sys
import pandas as pd

# Add the parent directory to sys.path to ensure absolute imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itas.settings")
import django
django.setup()

from ai_training.external_dataset_loader import ExternalDatasetLoader
from ai_training.dataset_normalizer import DatasetNormalizer
from ai_training.dataset_cleaner import DatasetCleaner
from ai_training.dataset_validator import DatasetValidator
from ai_training.feature_builder import FeatureBuilder
from ai_training.dataset_merger import DatasetMerger
from core.models import CV

def collect_local_resumes():
    resumes = []
    for cv in CV.objects.all():
        resumes.append({
            "source": "local_db",
            "raw_text": cv.extracted_text or "",
            "domain": cv.employee.title if cv.employee else ""
        })
    return pd.DataFrame(resumes)

def run_pipeline():
    print("Starting Data Pipeline...")
    
    loader = ExternalDatasetLoader()
    ext_path = loader.fetch_all()
    
    if ext_path:
        ext_df = pd.read_csv(ext_path)
    else:
        ext_df = pd.DataFrame()
        
    local_df = collect_local_resumes()
    
    df = pd.concat([ext_df, local_df], ignore_index=True)
    print(f"Total raw resumes collected: {len(df)}")
    
    normalizer = DatasetNormalizer()
    normalized_records = [normalizer.normalize_resume(row.to_dict()) for _, row in df.iterrows()]
    df = pd.DataFrame(normalized_records)
    
    cleaner = DatasetCleaner()
    df = cleaner.clean_resumes(df)
    
    feature_builder = FeatureBuilder()
    df = feature_builder.process_dataframe(df)
    
    validator = DatasetValidator()
    is_valid, err = validator.validate_dataset(df)
    if not is_valid:
        print(f"Dataset validation failed: {err}")
    else:
        print("Dataset validation passed.")
        
    # Drop rows that failed skill extraction
    df = df[df['skills'].apply(lambda x: isinstance(x, list) and len(x) > 0)]
    print(f"After removing resumes with 0 skills: {len(df)}")
    
    merger = DatasetMerger()
    merger.generate_splits(df)
    print("Data Pipeline Completed.")

if __name__ == "__main__":
    run_pipeline()
