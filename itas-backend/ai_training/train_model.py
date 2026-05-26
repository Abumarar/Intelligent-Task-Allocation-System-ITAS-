import os

import joblib
import kagglehub
import pandas as pd
from kagglehub import KaggleDatasetAdapter
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

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
    if "Resume" in df.columns:
        df["cleaned_text"] = df["Resume"].apply(clean_text)
    elif "Resume_str" in df.columns:
        df["cleaned_text"] = df["Resume_str"].apply(clean_text)
    else:
        # Fallback
        text_col = [
            c for c in df.columns if "resume" in c.lower() or "text" in c.lower()
        ]
        if text_col:
            df["cleaned_text"] = df[text_col[0]].apply(clean_text)
        else:
            raise ValueError("Could not identify Resume text column")

    return df


def train():
    """
    Main training workflow for the resume classification model.
    1. Loads dataset
    2. Preprocesses text (cleaning, missing values)
    3. Splits data into train and test sets
    4. Extracts features using TF-IDF (word and char n-grams)
    5. Trains a Calibrated LinearSVC model
    6. Evaluates with accuracy, classification report, and confusion matrix
    7. Saves the model using joblib
    """
    try:
        # 1. Load data
        df = load_data()

        label_col = "Category"
        if label_col not in df.columns:
            candidates = [
                c for c in df.columns if "category" in c.lower() or "label" in c.lower()
            ]
            if not candidates:
                raise ValueError("Could not identify Category/label column")
            label_col = candidates[0]

        # 2. Handle missing values
        print("Handling missing values...")
        df.dropna(subset=["cleaned_text", label_col], inplace=True)

        # Encode categorical labels if they are not string (they usually are in this dataset)
        df[label_col] = df[label_col].astype(str)

        print("\nDataset Stats:")
        print(df[label_col].value_counts())

        # 3. Prepare X and y
        X = df["cleaned_text"]
        y = df[label_col]

        # Train/test split with stratification to maintain class distribution
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(
            f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples..."
        )

        # 4. Feature Extraction & Pipeline setup
        # Use Word and Character n-grams for robust text representation
        word_vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=40000,
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True,
        )
        char_vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=2
        )
        features = FeatureUnion(
            [
                ("word", word_vectorizer),
                ("char", char_vectorizer),
            ]
        )

        # 5. Train Model
        # LinearSVC is fast and effective for sparse text data
        base_clf = LinearSVC(random_state=42, class_weight="balanced")
        # CalibratedClassifierCV allows us to get probability estimates (predict_proba)
        calibrated_clf = CalibratedClassifierCV(base_clf, method="sigmoid", cv=3)

        pipeline = Pipeline([("features", features), ("clf", calibrated_clf)])

        print("Training model (this might take a minute)...")
        pipeline.fit(X_train, y_train)

        # 6. Evaluation
        print("Evaluating model...")
        predictions = pipeline.predict(X_test)

        print("\nModel Evaluation:")
        print(classification_report(y_test, predictions))
        print(f"Accuracy: {accuracy_score(y_test, predictions):.3f}")
        print(f"Macro F1: {f1_score(y_test, predictions, average='macro'):.3f}")

        # Confusion Matrix
        import numpy as np
        from sklearn.metrics import confusion_matrix

        cm = confusion_matrix(y_test, predictions)
        print("\nConfusion Matrix:")
        print(cm)

        # 7. Save model
        model_path = os.path.join(
            os.path.dirname(__file__), "resume_classifier_model.pkl"
        )
        joblib.dump(pipeline, model_path)
        print(f"\nModel saved to {model_path}")

        return pipeline

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    train()
