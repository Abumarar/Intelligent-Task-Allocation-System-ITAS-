import sys
import os

# Ensure the parent directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_training.trainers.skill_predictor import SkillPredictorTrainer
from ai_training.trainers.matching_model import MatchingModelTrainer

def run_training():
    print("Starting ML Training Pipeline...")
    
    # 1. Train Skill/Domain Predictor
    skill_trainer = SkillPredictorTrainer()
    skill_trainer.train()
    
    # 2. Train Matching Models
    matching_trainer = MatchingModelTrainer()
    
    # Phase 1: TF-IDF
    matching_trainer.train_tfidf_baseline()
    
    # Phase 2: Sentence Transformers & LightGBM
    matching_trainer.download_sentence_transformers()
    matching_trainer.train_lightgbm_ranker()
    
    print("Training Pipeline Completed.")

if __name__ == "__main__":
    run_training()
