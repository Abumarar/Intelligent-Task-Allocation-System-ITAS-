"""
Shared text preprocessing for resume classification.
Keeps key tech tokens while normalizing noisy input.
"""
import re
import unicodedata


TOKEN_REPLACEMENTS = {
    "c++": "cplusplus",
    "c#": "csharp",
    "asp.net": "aspnet",
    ".net": "dotnet",
    "node.js": "nodejs",
    "react.js": "reactjs",
    "vue.js": "vuejs",
    "next.js": "nextjs",
    "nuxt.js": "nuxtjs",
    "ci/cd": "cicd",
    "ci-cd": "cicd",
}


def clean_text(text: str) -> str:
    """Normalize resume text for model training/inference."""
    if not isinstance(text, str):
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.lower()

    for src, dest in TOKEN_REPLACEMENTS.items():
        normalized = normalized.replace(src, dest)

    normalized = re.sub(r"http\S+\s*", " ", normalized)
    normalized = re.sub(r"@[^\s]+", " ", normalized)
    normalized = re.sub(r"#\S+", " ", normalized)
    normalized = re.sub(r"\brt\b|\bcc\b", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized
