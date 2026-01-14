import os
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import LinearSVC
import joblib

import kagglehub
from kagglehub import KaggleDatasetAdapter

from core.services.text_preprocessor import clean_text

def _load_local_dataset():
    env_path = os.environ.get("RESUME_DATASET_PATH")
    candidates = [
        env_path,
        os.path.join("dataset", "UpdatedResumeDataSet.csv"),
        os.path.join("dataset", "ResumeDataset.csv"),
        os.path.join("dataset", "ResumeDataSet.csv"),
    ]

    for path in candidates:
        if path and os.path.exists(path):
            print(f"Loading local dataset from {path}...")
            return pd.read_csv(path)

    return None


def load_data():
    df = _load_local_dataset()
    if df is None:
        print("Downloading dataset from Kaggle...")
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "gauravduttakiit/resume-dataset",
            "UpdatedResumeDataSet.csv",
        )
    
    print("\nColumns:", df.columns)
    
    print("Cleaning text...")
    if 'Resume' in df.columns:
        df['cleaned_text'] = df['Resume'].apply(clean_text)
    elif 'Resume_str' in df.columns:
        df['cleaned_text'] = df['Resume_str'].apply(clean_text)
    else:
        # Fallback
        text_col = [c for c in df.columns if 'resume' in c.lower() or 'text' in c.lower()]
        if text_col:
            df['cleaned_text'] = df[text_col[0]].apply(clean_text)
        else:
            raise ValueError("Could not identify Resume text column")
    
    return df

def train():
    try:
        df = load_data()
        
        label_col = "Category"
        if label_col not in df.columns:
            candidates = [c for c in df.columns if "category" in c.lower() or "label" in c.lower()]
            if not candidates:
                raise ValueError("Could not identify Category/label column")
            label_col = candidates[0]

        print("\nDataset Stats:")
        print(df[label_col].value_counts())

        # Prepare X and y
        X = df['cleaned_text']
        y = df[label_col]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples...")
        
        # Create Pipeline
        word_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=40000,
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True
        )
        char_vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            min_df=2
        )
        features = FeatureUnion([
            ('word', word_vectorizer),
            ('char', char_vectorizer),
        ])
        base_clf = LinearSVC(random_state=42, class_weight='balanced')
        calibrated_clf = CalibratedClassifierCV(base_clf, method='sigmoid', cv=3)
        pipeline = Pipeline([
            ('features', features),
            ('clf', calibrated_clf)
        ])
        
        pipeline.fit(X_train, y_train)
        
        predictions = pipeline.predict(X_test)
        
        print("\nModel Evaluation:")
        print(classification_report(y_test, predictions))
        print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
        print(f"Macro F1: {f1_score(y_test, predictions, average='macro'):.3f}")
        
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
