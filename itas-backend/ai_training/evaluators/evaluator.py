from sklearn.metrics import accuracy_score, f1_score, classification_report
import numpy as np

class ModelEvaluator:
    @staticmethod
    def evaluate_classification(y_true, y_pred, y_prob=None):
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "f1_macro": f1_score(y_true, y_pred, average="macro"),
            "f1_weighted": f1_score(y_true, y_pred, average="weighted")
        }
        report = classification_report(y_true, y_pred)
        return metrics, report

    @staticmethod
    def evaluate_ranking(y_true, y_pred_scores, k=5):
        order = np.argsort(y_pred_scores)[::-1]
        try:
            top_k = y_true.iloc[order][:k].values
        except AttributeError:
            top_k = np.array(y_true)[order][:k]
            
        precision_at_k = np.sum(top_k) / min(k, len(top_k)) if len(top_k) > 0 else 0
        return {"precision_at_k": precision_at_k}
