import os
import pandas as pd
import numpy as np
import joblib

class RankerPredictor:
    """Wrapper for the LightGBM Ranker model."""
    
    def __init__(self):
        self.model = None
        # Load the local joblib artifact we saved during training
        model_path = os.path.join(os.path.dirname(__file__), "../../../ai_training/models/lgbm_ranker.pkl")
        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print(f"Loaded LightGBM model from {model_path}")
            else:
                print(f"Warning: Model not found at {model_path}. Using heuristics.")
        except Exception as e:
            print(f"Error loading model: {e}. Using heuristics.")
        
    def predict(self, features_df: pd.DataFrame) -> np.ndarray:
        """Predicts suitability scores."""
        if features_df is None or features_df.empty:
            return np.array([])
            
        if self.model is None:
            # Fallback heuristic if no model is loaded yet
            return (
                features_df["skill_overlap_ratio"] * 0.4 +
                features_df.get("semantic_match_score", 0.0) * 0.3 +
                features_df.get("average_rating", 3.0) / 5.0 * 0.2 +
                features_df.get("availability_score", 1.0) * 0.1
            ).values
            
        # The trained model expects specific feature names in a specific order:
        expected_features = [
            "skill_overlap",
            "critical_skill_match",
            "missing_required_skills",
            "years_experience",
            "similar_tasks_completed",
            "active_tasks",
            "workload_percentage",
            "availability_score",
            "github_activity_score",
            "average_rating",
            "historical_success_rate"
        ]
        
        # Map feature store keys to expected keys if they differ
        # E.g. skill_overlap_ratio -> skill_overlap
        rename_map = {
            "skill_overlap_ratio": "skill_overlap",
            "current_workload_pct": "workload_percentage"
        }
        df = features_df.rename(columns=rename_map)
        
        # Fill missing features with defaults to prevent crashes
        for col in expected_features:
            if col not in df.columns:
                df[col] = 0.0
                
        # We must predict exactly on the features the model was trained on
        preds = self.model.predict(df[expected_features])
        return preds
