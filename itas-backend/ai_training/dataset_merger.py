import pandas as pd
from sklearn.model_selection import train_test_split
import os

class DatasetMerger:
    def __init__(self, output_dir="ai_training/data/processed"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_splits(self, df, target_col="domain"):
        print(f"Generating splits for {len(df)} records...")
        if df.empty:
            return None, None, None
            
        stratify_col = None
        if target_col in df.columns and df[target_col].nunique() > 1:
            counts = df[target_col].value_counts()
            valid_domains = counts[counts > 5].index
            df = df[df[target_col].isin(valid_domains)]
            if len(df) > 10:
                stratify_col = df[target_col]
        
        if len(df) < 10:
            print("Dataset too small for train_test_split. Creating minimal splits.")
            train_path = os.path.join(self.output_dir, "train.csv")
            df.to_csv(train_path, index=False)
            return train_path, None, None
            
        train_df, temp_df = train_test_split(
            df, test_size=0.3, random_state=42, stratify=stratify_col
        )
        
        val_strat = temp_df[target_col] if stratify_col is not None else None
        try:
            val_df, test_df = train_test_split(
                temp_df, test_size=0.5, random_state=42, stratify=val_strat
            )
        except:
            val_df, test_df = train_test_split(
                temp_df, test_size=0.5, random_state=42
            )
            
        train_path = os.path.join(self.output_dir, "train.csv")
        val_path = os.path.join(self.output_dir, "val.csv")
        test_path = os.path.join(self.output_dir, "test.csv")
        
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        print(f"Saved splits: Train {len(train_df)}, Val {len(val_df)}, Test {len(test_df)}")
        return train_path, val_path, test_path
