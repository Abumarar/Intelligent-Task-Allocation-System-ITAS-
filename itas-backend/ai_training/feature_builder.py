import os
import sys
import pandas as pd

# Ensure django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itas.settings")
import django
if not django.apps.apps.ready:
    django.setup()

from core.services.skill_extractor import SkillExtractor
from core.services.text_preprocessor import clean_text

class FeatureBuilder:
    def __init__(self):
        self.skill_extractor = SkillExtractor()

    def extract_features_from_resume(self, text):
        cleaned = clean_text(text)
        skills = self.skill_extractor.extract_skills(cleaned)
        skill_names = [s['name'] for s in skills]
        return {
            "clean_text": cleaned,
            "extracted_skills": skill_names
        }

    def process_dataframe(self, df):
        if df is None or df.empty:
            return df
            
        features = []
        for _, row in df.iterrows():
            feat = self.extract_features_from_resume(row.get("raw_text", ""))
            features.append(feat)
        
        df['clean_text'] = [f['clean_text'] for f in features]
        if 'skills' not in df.columns:
            df['skills'] = [f['extracted_skills'] for f in features]
        else:
            df['skills'] = df.apply(
                lambda x: x['skills'] if isinstance(x.get('skills'), list) and len(x.get('skills', [])) > 0 
                else features[x.name]['extracted_skills'], axis=1
            )
        
        return df
