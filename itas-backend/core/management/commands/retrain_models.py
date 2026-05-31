import os
import json
import hashlib
from datetime import datetime
from django.core.management.base import BaseCommand
from ai_training.data_pipeline import run_pipeline
from ai_training.train_model import run_training
from ai_training.configs.training_config import Config

class Command(BaseCommand):
    help = 'Executes the full data pipeline and retrains all ML models.'

    def handle(self, *args, **options):
        self.stdout.write("Starting Retraining Process...")
        
        # 1. Run pipeline to fetch/process data
        self.stdout.write("Running Data Pipeline...")
        run_pipeline()
        
        # Hash training data for versioning
        train_csv_path = Config.TRAIN_DATA
        dataset_hash = ""
        if os.path.exists(train_csv_path):
            with open(train_csv_path, 'rb') as f:
                dataset_hash = hashlib.md5(f.read()).hexdigest()
                
        # 2. Train models
        self.stdout.write("Running Model Training...")
        run_training()
        
        # 3. Save Model Versioning Metadata
        version_data = {
            "version": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "dataset_hash": dataset_hash,
            "trained_at": datetime.utcnow().isoformat(),
        }
        
        version_file = os.path.join(Config.MODELS_DIR, "version.json")
        with open(version_file, "w") as f:
            json.dump(version_data, f, indent=4)
            
        self.stdout.write(self.style.SUCCESS(f"Retraining complete. Version metadata saved: {version_data['version']}"))
