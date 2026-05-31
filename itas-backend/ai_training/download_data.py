import sys
import os

# Ensure the parent directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_training.data_pipeline import run_pipeline

if __name__ == "__main__":
    print("Executing dataset orchestration pipeline...")
    run_pipeline()
