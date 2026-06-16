from sklearn.metrics import accuracy_score, f1_score, classification_report
import numpy as np

class ModelEvaluator:
    @staticmethod
    def evaluate_classification(y_true, y_pred):
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "f1_macro": f1_score(y_true, y_pred, average="macro"),
            "f1_weighted": f1_score(y_true, y_pred, average="weighted")
        }
        report = classification_report(y_true, y_pred)
        return metrics, report

