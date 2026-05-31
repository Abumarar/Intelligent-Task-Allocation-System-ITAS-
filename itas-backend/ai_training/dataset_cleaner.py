import pandas as pd
from rapidfuzz import fuzz
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

class DatasetCleaner:
    def __init__(self):
        pass
        
    def clean_resumes(self, df):
        if df is None or df.empty:
            return df
            
        print(f"Initial resumes for cleaning: {len(df)}")
        
        # 1. Drop missing raw_text
        df = df.dropna(subset=['raw_text'])
        df = df[df['raw_text'].str.len() > 100]
        
        # 2. Filter by language (Keep only English)
        def is_english(text):
            try:
                return detect(text[:1000]) == 'en'
            except:
                return False
                
        df['is_en'] = df['raw_text'].apply(is_english)
        df = df[df['is_en'] == True].drop(columns=['is_en'])
        print(f"After language filter: {len(df)}")
        
        # 3. Exact deduplication
        df = df.drop_duplicates(subset=['raw_text'])
        print(f"After exact deduplication: {len(df)}")
        
        return df
