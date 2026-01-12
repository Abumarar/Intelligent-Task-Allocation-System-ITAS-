import kagglehub
import os
import shutil

# Download latest version
print("Downloading dataset...")
path = kagglehub.dataset_download("palaksood97/resume-dataset")

print("Path to dataset files:", path)

# List files in the downloaded directory
files = os.listdir(path)
print("Files in dataset:", files)

# Copy to current directory for easier access
target_dir = os.getcwd()
for file in files:
    source_file = os.path.join(path, file)
    target_file = os.path.join(target_dir, "dataset", file)
    
    # Create dataset dir if not exists
    os.makedirs(os.path.join(target_dir, "dataset"), exist_ok=True)
    
    if os.path.isfile(source_file):
        shutil.copy2(source_file, target_file)
        print(f"Copied file {file}")
    elif os.path.isdir(source_file):
        if os.path.exists(target_file):
            shutil.rmtree(target_file)
        shutil.copytree(source_file, target_file)
        print(f"Copied directory {file}")
