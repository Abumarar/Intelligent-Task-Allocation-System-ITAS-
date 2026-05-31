import pytest
from core.services.ml.inference_pipeline import InferencePipeline

def test_inference_pipeline_similarity():
    pipeline = InferencePipeline()
    sim = pipeline.calculate_similarity("python developer", "python developer")
    assert isinstance(sim, float)
