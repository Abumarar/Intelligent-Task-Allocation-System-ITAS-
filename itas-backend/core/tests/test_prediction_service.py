import pytest
from core.services.prediction_service import PredictionService

def test_predict_category_empty():
    prediction = PredictionService.predict_category("")
    assert isinstance(prediction, str)

def test_predict_category_proba_empty():
    proba = PredictionService.predict_category_proba("")
    assert isinstance(proba, dict)
