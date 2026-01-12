import os
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib

import kagglehub
import glob

def clean_text(text):
    """
    Basic text cleaning: remove special characters, extra spaces.
    """
    if not isinstance(text, str):
        return ""
    
    text = re.sub(r'http\S+\s*', ' ', text)  # remove URLs
    text = re.sub(r'RT|cc', ' ', text)  # remove RT and cc
    text = re.sub(r'#\S+', '', text)  # remove hashtags
    text = re.sub(r'@\S+', '  ', text)  # remove mentions
    text = re.sub(r'[^\x00-\x7f]', r' ', text)  # remove non-ascii characters (optional)
    text = re.sub(r'\s+', ' ', text).strip()  # remove extra whitespace
    return text

def load_data():
    print("Downloading dataset from Kaggle...")
    # Download latest version using kagglehub
    path = kagglehub.dataset_download("gauravduttakiit/resume-dataset")
    print("Path to dataset files:", path)
    
    # Find the CSV file in the downloaded directory
    csv_files = glob.glob(os.path.join(path, "*.csv"))
    if not csv_files:
        # Recursive search if not in root
        csv_files = glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)
        
    if not csv_files:
         raise FileNotFoundError(f"No CSV file found in {path}")
         
    csv_path = csv_files[0]
    print(f"Loading dataset from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    # Rename for consistency if needed, but we'll specific columns
    print(f"Columns: {df.columns}")
    
    # Clean text
    print("Cleaning text...")
    if 'Resume_str' in df.columns:
        df['cleaned_text'] = df['Resume_str'].apply(clean_text)
    elif 'Resume' in df.columns:
         df['cleaned_text'] = df['Resume'].apply(clean_text)
    else:
        # Fallback to finding text column
        text_col = [c for c in df.columns if 'resume' in c.lower() or 'text' in c.lower()]
        if text_col:
            df['cleaned_text'] = df[text_col[0]].apply(clean_text)
        else:
             raise ValueError("Could not identify Resume text column")
    
    return df

def train():
    try:
        df = load_data()
        
        print("\nDataset Stats:")
        print(df['Category'].value_counts())
        
        # Prepare X and y
        X = df['cleaned_text']
        y = df['Category']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples...")
        
        # Create Pipeline
        # Increasing max_features as we have more data and varied text
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 2))),
            ('clf', LinearSVC(random_state=42, dual='auto'))
        ])
        
        pipeline.fit(X_train, y_train)
        
        predictions = pipeline.predict(X_test)
        
        print("\nModel Evaluation:")
        print(classification_report(y_test, predictions))
        print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
        
        # Save model
        model_path = "resume_classifier_model.pkl"
        joblib.dump(pipeline, model_path)
        print(f"\nModel saved to {model_path}")
        
        return pipeline
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    train()
