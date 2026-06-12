import pandas as pd
import numpy as np
import joblib
import mlflow
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import lightgbm as lgb
from sentence_transformers import SentenceTransformer

from ai_training.configs.training_config import Config

class MatchingModelTrainer:
    def __init__(self, config=Config):
        self.config = config
        os.makedirs(self.config.MODELS_DIR, exist_ok=True)
        mlflow.set_tracking_uri(self.config.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("Matching_Model_Experiment")

    def train_tfidf_baseline(self):
        print("Training TF-IDF Baseline Matching Model...")
        if not os.path.exists(self.config.TRAIN_DATA):
            print("No training data found.")
            return None
            
        train_df = pd.read_csv(self.config.TRAIN_DATA)
        train_df = train_df.dropna(subset=['clean_text'])
        if train_df.empty:
            print("No valid training data for TF-IDF baseline.")
            return None
        
        with mlflow.start_run(run_name="TFIDF_Matching"):
            vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
            vectorizer.fit(train_df['clean_text'])
            
            model_path = os.path.join(self.config.MODELS_DIR, "tfidf_matching_vectorizer.pkl")
            joblib.dump(vectorizer, model_path)
            mlflow.log_artifact(model_path)
            print(f"TF-IDF Vectorizer saved to {model_path}")
            
        return vectorizer

    def train_lightgbm_ranker(self):
        print("Training LightGBM Ranking Model (Phase 2)...")
        dataset_path = "ai_training/dataset/task_assignment_training_dataset.csv"
        
        if not os.path.exists(dataset_path):
            print(f"No task assignment data found at {dataset_path}. Run generate_data.py first.")
            return None
            
        print(f"Loading data from {dataset_path}...")
        df = pd.read_csv(dataset_path)
        
        # LGBMRanker requires the data to be sorted by the group identifier (task_id)
        df = df.sort_values('task_id')
        
        features = [
            'skill_overlap', 'critical_skill_match', 'missing_required_skills',
            'years_experience', 'similar_tasks_completed', 'active_tasks',
            'workload_percentage', 'availability_score', 'github_activity_score',
            'average_rating', 'historical_success_rate'
        ]
        
        X_train = df[features]
        # LightGBM lambdarank expects relevance labels to be integers from 0 to 31.
        # We will bin the 0-100 performance score into 5 relevance levels (0 to 4).
        y_train = (df['performance_score'] // 20).clip(0, 4).astype(int)
        
        # Create group array (number of items per task_id)
        group = df.groupby('task_id').size().values
        
        with mlflow.start_run(run_name="LightGBM_Ranking"):
            print(f"Fitting LightGBM Ranker on {len(df)} samples...")
            model = lgb.LGBMRanker(
                objective="lambdarank",
                metric="ndcg",
                n_estimators=100,
                learning_rate=0.1,
                random_state=self.config.RANDOM_STATE
            )
            
            model.fit(X_train, y_train, group=group)
            
            model_path = os.path.join(self.config.MODELS_DIR, "lgbm_ranker.pkl")
            joblib.dump(model, model_path)
            
            mlflow.log_param("model_type", "LGBMRanker")
            mlflow.log_param("objective", "lambdarank")
            mlflow.log_param("n_samples", len(df))
            mlflow.log_param("n_features", len(features))
            print(f"LightGBM Ranker fitted and saved to {model_path}")
            
        return model

    def download_sentence_transformers(self):
        print("Downloading SentenceTransformer model...")
        with mlflow.start_run(run_name="SentenceTransformer_Download"):
            # Using a smaller model for faster execution in limited environments
            model = SentenceTransformer('all-MiniLM-L6-v2')
            model_path = os.path.join(self.config.MODELS_DIR, "sentence_transformer")
            model.save(model_path)
            mlflow.log_param("model_name", "all-MiniLM-L6-v2")
            print(f"SentenceTransformer saved to {model_path}")
        return model
