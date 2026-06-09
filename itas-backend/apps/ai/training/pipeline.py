import os
import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
import mlflow
import mlflow.lightgbm
from sklearn.model_selection import GroupShuffleSplit

# File paths
DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../ai_training/dataset/task_assignment_training_dataset.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../../../ai_training/models")

def load_and_prepare_data():
    """Loads dataset and prepares it for LightGBM Ranker."""
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    
    # LightGBM Ranker REQUIRES data to be sorted by the group key (task_id)
    df = df.sort_values(by="task_id").reset_index(drop=True)
    
    # LambdaMART expects integer relevance labels (typically 0-4)
    # We will bin the continuous performance_score (0-100) into 5 relevance levels:
    # 0-30: 0 (Poor)
    # 31-50: 1 (Fair)
    # 51-70: 2 (Good)
    # 71-85: 3 (Very Good)
    # 86-100: 4 (Excellent)
    bins = [-1, 30, 50, 70, 85, 100]
    labels = [0, 1, 2, 3, 4]
    df['relevance'] = pd.cut(df['performance_score'], bins=bins, labels=labels).astype(int)
    
    features = [
        "skill_overlap",
        "critical_skill_match",
        "missing_required_skills",
        "years_experience",
        "similar_tasks_completed",
        "active_tasks",
        "workload_percentage",
        "availability_score",
        "github_activity_score",
        "average_rating",
        "historical_success_rate"
    ]
    
    return df, features

def train_ranker():
    df, features = load_and_prepare_data()
    
    # We must split by task_id (group) so all candidates for a task stay in the same split
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, val_idx = next(gss.split(df, groups=df['task_id']))
    
    train_df = df.iloc[train_idx]
    val_df = df.iloc[val_idx]
    
    X_train = train_df[features]
    y_train = train_df['relevance']
    group_train = train_df.groupby('task_id').size().values
    
    X_val = val_df[features]
    y_val = val_df['relevance']
    group_val = val_df.groupby('task_id').size().values
    
    print(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples.")
    
    # LightGBM Ranker parameters
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [1, 3, 5],
        'learning_rate': 0.05,
        'num_leaves': 31,
        'min_data_in_leaf': 20,
        'n_estimators': 200,
        'random_state': 42
    }
    
    # MLflow tracking
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../mlflow.db"))
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")
    mlflow.set_experiment("ITAS_Candidate_Ranker")
    
    with mlflow.start_run():
        print("Training LightGBM Ranker...")
        ranker = lgb.LGBMRanker(**params)
        
        ranker.fit(
            X_train, y_train,
            group=group_train,
            eval_set=[(X_val, y_val)],
            eval_group=[group_val],
            callbacks=[lgb.early_stopping(stopping_rounds=20)]
        )
        
        # Log model & params to MLflow
        mlflow.lightgbm.log_model(ranker, "model")
        mlflow.log_params(params)
        
        # Save a local fallback joblib copy
        os.makedirs(MODEL_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_DIR, "lgbm_ranker.pkl")
        joblib.dump(ranker, model_path)
        
        print(f"Model successfully trained and saved to {model_path} and registered in MLflow.")
        
        # Feature Importance
        importance = ranker.feature_importances_
        feature_importance = pd.DataFrame({'feature': features, 'importance': importance})
        feature_importance = feature_importance.sort_values(by='importance', ascending=False)
        print("\nFeature Importances:")
        print(feature_importance.to_string(index=False))

if __name__ == "__main__":
    train_ranker()
