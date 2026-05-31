from core.services.ml.inference_pipeline import InferencePipeline

class PredictionService:
    """
    Abstraction layer for loading the AI model and making predictions.
    Updated to use the new ML Service Layer infrastructure.
    """

    _pipeline = InferencePipeline()

    @classmethod
    def get_model(cls):
        """Backward compatibility: Get model directly from registry if needed."""
        from core.services.ml.model_registry import ModelRegistry
        return ModelRegistry.get_model("domain_predictor", fallback_path="ai_training/resume_classifier_model.pkl")

    @classmethod
    def predict_category(cls, text: str) -> str:
        """Predict the category/role for a given text."""
        result = cls._pipeline.predict_domain(text)
        return result.get("prediction", "")

    @classmethod
    def predict_category_proba(cls, text: str) -> dict:
        """Predict the category probabilities for a given text."""
        result = cls._pipeline.predict_domain(text)
        return result.get("probabilities", {})
