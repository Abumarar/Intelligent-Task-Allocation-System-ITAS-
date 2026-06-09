import pandas as pd
import numpy as np

class RankerPredictor:
    """Wrapper for the LightGBM Ranker model via MLflow."""
    
    def __init__(self):
        self.model = None
        # In a real scenario, this would load from MLflow registry:
        # self.model = mlflow.lightgbm.load_model("models:/CandidateRanker/Production")
        
    def predict(self, features_df: pd.DataFrame) -> np.ndarray:
        """Predicts suitability scores."""
        if features_df is None or features_df.empty:
            return np.array([])
            
        if self.model is None:
            # Fallback heuristic if no model is loaded yet
            # Weights applied to the engineered features
            return (
                features_df["skill_overlap_ratio"] * 0.4 +
                features_df["semantic_match_score"] * 0.3 +
                features_df["average_rating"] / 5.0 * 0.2 +
                features_df["availability_score"] * 0.1
            ).values
            
        return self.model.predict(features_df)
