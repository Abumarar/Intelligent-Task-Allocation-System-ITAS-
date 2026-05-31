import os
import joblib
from functools import lru_cache

class ModelRegistry:
    """Registry for lazy loading and caching ML models."""
    
    _models = {}
    _base_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "ai_training", "models"
    )

    @classmethod
    def get_model(cls, model_name: str, fallback_path: str = None):
        """Lazy load a model by name with caching."""
        if model_name in cls._models:
            return cls._models[model_name]

        # Standard model path
        model_path = os.path.join(cls._base_path, f"{model_name}.pkl")
        
        if not os.path.exists(model_path):
            if fallback_path and os.path.exists(fallback_path):
                model_path = fallback_path
            else:
                # Also check root ai_training dir for legacy models
                legacy_path = os.path.join(os.path.dirname(cls._base_path), f"{model_name}.pkl")
                if os.path.exists(legacy_path):
                    model_path = legacy_path
                else:
                    return None

        try:
            model = joblib.load(model_path)
            cls._models[model_name] = model
            return model
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None

    @classmethod
    def get_sentence_transformer(cls):
        """Lazy load sentence transformer."""
        model_name = "sentence_transformer"
        if model_name in cls._models:
            return cls._models[model_name]
            
        model_path = os.path.join(cls._base_path, model_name)
        if not os.path.exists(model_path):
            return None
            
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_path)
            cls._models[model_name] = model
            return model
        except Exception as e:
            print(f"Error loading SentenceTransformer: {e}")
            return None

    @classmethod
    def clear_cache(cls):
        """Clear model cache to free memory or reload."""
        cls._models.clear()
