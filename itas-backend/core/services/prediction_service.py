import os

import joblib


class PredictionService:
    """
    Abstraction layer for loading the AI model and making predictions.
    This separates the ML inference logic from standard Django views.
    """

    _model = None

    @classmethod
    def get_model(cls):
        """Lazy load the model to avoid loading it on every request."""
        if cls._model is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "ai_training",
                "resume_classifier_model.pkl",
            )
            if not os.path.exists(model_path):
                # Optionally train or return None
                print(f"Model not found at {model_path}")
                return None
            cls._model = joblib.load(model_path)
        return cls._model

    @classmethod
    def predict_category(cls, text: str) -> str:
        """
        Predict the category/role for a given text.
        """
        model = cls.get_model()
        if not model:
            return ""

        try:
            prediction = model.predict([text])
            return str(prediction[0])
        except Exception as e:
            print(f"Error predicting category: {e}")
            return ""

    @classmethod
    def predict_category_proba(cls, text: str) -> dict:
        """
        Predict the category probabilities for a given text.
        """
        model = cls.get_model()
        if not model:
            return {}

        try:
            probabilities = model.predict_proba([text])[0]
            classes = model.classes_
            return dict(zip(classes, probabilities))
        except Exception as e:
            print(f"Error predicting probabilities: {e}")
            return {}
