import pandas as pd
from core.services.ml.inference_pipeline import InferencePipeline

class RegressionValidator:
    def __init__(self):
        self.pipeline = InferencePipeline()

    def validate_determinism(self, text: str):
        pred1 = self.pipeline.predict_domain(text)
        pred2 = self.pipeline.predict_domain(text)
        assert pred1['prediction'] == pred2['prediction'], "Prediction drift detected!"
        assert pred1['confidence'] == pred2['confidence'], "Confidence drift detected!"
        return True

    def validate_schema(self, dataset_path):
        df = pd.read_csv(dataset_path)
        required_cols = ["clean_text"]
        for col in required_cols:
            assert col in df.columns, f"Schema mismatch: missing {col}"
        return True
