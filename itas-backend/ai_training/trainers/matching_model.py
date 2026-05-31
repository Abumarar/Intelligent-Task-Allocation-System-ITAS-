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
        with mlflow.start_run(run_name="LightGBM_Ranking"):
            # We instantiate the ranker architecture to have the model artifact ready
            # In a real environment with task-assignment pairs, we would fit it here
            model = lgb.LGBMRanker(
                objective="lambdarank",
                metric="ndcg",
                n_estimators=100,
                learning_rate=0.1,
                random_state=self.config.RANDOM_STATE
            )
            
            # Save dummy model for architecture completeness
            model_path = os.path.join(self.config.MODELS_DIR, "lgbm_ranker.pkl")
            joblib.dump(model, model_path)
            
            mlflow.log_param("model_type", "LGBMRanker")
            mlflow.log_param("objective", "lambdarank")
            print(f"LightGBM Ranker architecture saved to {model_path}")
            
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
