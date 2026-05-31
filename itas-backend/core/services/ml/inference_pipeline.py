from typing import Dict, Any, List
from core.services.ml.model_registry import ModelRegistry
from core.services.ml.feature_transformer import FeatureTransformer

class InferencePipeline:
    """High-level pipeline for running model inference."""
    
    def __init__(self):
        self.feature_transformer = FeatureTransformer()

    def predict_domain(self, text: str) -> Dict[str, Any]:
        """Predict domain/category for a given text."""
        model = ModelRegistry.get_model("domain_predictor", fallback_path="ai_training/resume_classifier_model.pkl")
        if not model:
            return {"prediction": "", "confidence": 0.0, "probabilities": {}}
            
        cleaned = self.feature_transformer.extract_features(text)["clean_text"]
        
        try:
            prediction = model.predict([cleaned])[0]
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba([cleaned])[0]
                classes = model.classes_
                prob_dict = dict(zip(classes, probs))
                confidence = float(prob_dict.get(prediction, 0.0))
                return {
                    "prediction": str(prediction),
                    "confidence": confidence,
                    "probabilities": {str(k): float(v) for k, v in prob_dict.items()}
                }
            return {"prediction": str(prediction), "confidence": 1.0, "probabilities": {}}
        except Exception as e:
            print(f"Error in predict_domain: {e}")
            return {"prediction": "", "confidence": 0.0, "probabilities": {}}

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts using TF-IDF baseline."""
        from sklearn.metrics.pairwise import cosine_similarity
        
        vec1 = self.feature_transformer.transform_text_to_tfidf(text1)
        vec2 = self.feature_transformer.transform_text_to_tfidf(text2)
        
        if vec1 is None or vec2 is None:
            return 0.0
            
        sim = cosine_similarity(vec1, vec2)[0][0]
        return float(sim)
        
    def rank_candidates(self, task_text: str, candidate_texts: List[str]) -> List[float]:
        """Rank candidates against a task using ML model (TF-IDF fallback currently)."""
        scores = []
        for cand in candidate_texts:
            scores.append(self.calculate_similarity(task_text, cand))
        return scores
