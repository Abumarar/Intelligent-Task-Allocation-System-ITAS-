import numpy as np
from sklearn.metrics import ndcg_score, roc_auc_score

def precision_at_k(y_true, y_pred, k=5):
    order = np.argsort(y_pred)[::-1]
    top_k = np.array(y_true)[order][:k]
    return np.sum(top_k) / min(k, len(top_k)) if len(top_k) > 0 else 0

def recall_at_k(y_true, y_pred, k=5):
    order = np.argsort(y_pred)[::-1]
    top_k = np.array(y_true)[order][:k]
    total_relevant = np.sum(y_true)
    return np.sum(top_k) / total_relevant if total_relevant > 0 else 0

def calculate_ndcg(y_true, y_pred, k=5):
    if len(y_true) < 2:
        return 0.0
    return ndcg_score([y_true], [y_pred], k=k)
    
def calculate_roc_auc(y_true, y_pred):
    if len(np.unique(y_true)) < 2:
        return 0.0
    return roc_auc_score(y_true, y_pred)
