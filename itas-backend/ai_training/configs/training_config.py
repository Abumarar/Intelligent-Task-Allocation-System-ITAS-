import os

class Config:
    MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    DATA_DIR = "ai_training/data/processed"
    MODELS_DIR = "ai_training/models"
    
    TRAIN_DATA = os.path.join(DATA_DIR, "train.csv")
    VAL_DATA = os.path.join(DATA_DIR, "val.csv")
    TEST_DATA = os.path.join(DATA_DIR, "test.csv")
    
    RANDOM_STATE = 42
