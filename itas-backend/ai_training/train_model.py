import os
import docx
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib

DATASET_DIR = "dataset/Resumes"

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def infer_label(filename):
    name = filename.lower()
    if re.search(r'java|j2ee', name):
        return 'Java Developer'
    elif re.search(r'pm|project manager|pmp|scrum master', name):
        return 'Project Manager'
    elif re.search(r'ba|business analyst|bsa', name):
        return 'Business Analyst'
    elif re.search(r'qa|testing|tester', name):
        return 'QA Engineer'
    elif re.search(r'php|web', name):
        return 'Web Developer'
    return 'Other'

def load_data():
    data = []
    labels = []
    
    files = [f for f in os.listdir(DATASET_DIR) if f.endswith('.docx')]
    print(f"Found {len(files)} resumes. Processing...")
    
    for filename in files:
        file_path = os.path.join(DATASET_DIR, filename)
        text = extract_text_from_docx(file_path)
        if text.strip():
            label = infer_label(filename)
            data.append(text)
            labels.append(label)
            
    return pd.DataFrame({'text': data, 'label': labels})

def train():
    print("Loading and creating dataset...")
    df = load_data()
    
    print("\nDataset Stats:")
    print(df['label'].value_counts())
    
    # Filter out classes with too few samples for stratification
    v_counts = df['label'].value_counts()
    df = df[df['label'].isin(v_counts[v_counts > 1].index)]
    
    print("\nFiltered Dataset Stats:")
    print(df['label'].value_counts())
    
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
    )
    
    print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples...")
    
    # Create Pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=3000)),
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

if __name__ == "__main__":
    train()
