import pandas as pd
import joblib
import mlflow
import os
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from ai_training.configs.training_config import Config
from ai_training.evaluators.evaluator import ModelEvaluator

class SkillPredictorTrainer:
    def __init__(self, config=Config):
        self.config = config
        os.makedirs(self.config.MODELS_DIR, exist_ok=True)
        mlflow.set_tracking_uri(self.config.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("Skill_Prediction_Experiment")

    def train(self):
        print("Training Skill/Domain Predictor...")
        if not os.path.exists(self.config.TRAIN_DATA):
            print(f"Training data not found at {self.config.TRAIN_DATA}")
            return None
            
        train_df = pd.read_csv(self.config.TRAIN_DATA)
        val_df = pd.read_csv(self.config.VAL_DATA) if os.path.exists(self.config.VAL_DATA) else None
        
        train_df = train_df.dropna(subset=['clean_text', 'domain'])
        if train_df.empty:
            print("No valid training data for Skill/Domain Predictor.")
            return None

        X_train = train_df['clean_text']
        y_train = train_df['domain']
        
        if val_df is not None:
            val_df = val_df.dropna(subset=['clean_text', 'domain'])
            if not val_df.empty:
                X_val = val_df['clean_text']
                y_val = val_df['domain']
            else:
                X_val, y_val = None, None
        else:
            X_val, y_val = None, None

        with mlflow.start_run(run_name="Logistic_Regression_Domain"):
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=10000, stop_words='english', ngram_range=(1,2))),
                ('clf', LogisticRegression(class_weight='balanced', random_state=self.config.RANDOM_STATE, max_iter=1000))
            ])
            
            pipeline.fit(X_train, y_train)
            
            if X_val is not None:
                preds = pipeline.predict(X_val)
                metrics, report = ModelEvaluator.evaluate_classification(y_val, preds)
                print("Validation Metrics:")
                for k, v in metrics.items():
                    print(f"{k}: {v:.4f}")
                    mlflow.log_metric(k, v)
                print("\nReport:\n", report)
                
            # Saving model to root ai_training dir to maintain backward compatibility 
            # with existing PredictionService before Phase 4 integration
            model_path = os.path.join("ai_training", "resume_classifier_model.pkl")
            joblib.dump(pipeline, model_path)
            mlflow.log_artifact(model_path)
            print(f"Model saved to {model_path}")
            
        return pipeline
