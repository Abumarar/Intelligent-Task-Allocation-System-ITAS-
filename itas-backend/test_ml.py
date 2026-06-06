from core.services.ml.model_registry import ModelRegistry
print("Getting model tfidf_matching_vectorizer...")
model = ModelRegistry.get_model("tfidf_matching_vectorizer")
print("Model returned:", model)
