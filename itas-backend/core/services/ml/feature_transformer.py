from core.services.text_preprocessor import clean_text
from core.services.skill_extractor import SkillExtractor
from core.services.ml.model_registry import ModelRegistry

class FeatureTransformer:
    """Transforms raw input text into model-ready features."""
    
    def __init__(self):
        self.skill_extractor = SkillExtractor()
        
    def transform_text_to_tfidf(self, text: str):
        """Transform text using the TF-IDF matching vectorizer."""
        vectorizer = ModelRegistry.get_model("tfidf_matching_vectorizer")
        if not vectorizer:
            return None
            
        cleaned = clean_text(text)
        return vectorizer.transform([cleaned])

    def transform_text_to_embedding(self, text: str):
        """Transform text into dense embeddings using SentenceTransformer."""
        model = ModelRegistry.get_sentence_transformer()
        if not model:
            return None
            
        cleaned = clean_text(text)
        return model.encode([cleaned])[0]
        
    def extract_features(self, text: str):
        """Extract basic features from text."""
        cleaned = clean_text(text)
        skills = self.skill_extractor.extract_skills(cleaned)
        return {
            "clean_text": cleaned,
            "skills": [s['name'] for s in skills]
        }
