"""
Skill Extraction Service using curated patterns and section heuristics.
Extracts technical skills from CV text using fast NLP-lite techniques.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set
import logging

try:
    import spacy
    from spacy.matcher import PhraseMatcher
except ImportError:
    spacy = None

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Service for extracting skills from CV text using NLP-lite heuristics."""

    TECHNICAL_SKILLS: Set[str] = {
        # Programming Languages
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "c",
        "go",
        "rust",
        "kotlin",
        "swift",
        "php",
        "ruby",
        "scala",
        "r",
        "matlab",
        "perl",
        "shell",
        "bash",
        "powershell",
        # Web Technologies
        "html",
        "css",
        "react",
        "vue",
        "angular",
        "svelte",
        "sveltekit",
        "node.js",
        "express",
        "django",
        "flask",
        "fastapi",
        "spring",
        "laravel",
        "asp.net",
        "jquery",
        "bootstrap",
        "sass",
        "less",
        "webpack",
        "vite",
        "tailwind",
        "redux",
        "next.js",
        "nuxt.js",
        # Databases
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "oracle",
        "sqlite",
        "cassandra",
        "elasticsearch",
        "dynamodb",
        "neo4j",
        "snowflake",
        "bigquery",
        # Cloud & DevOps
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "jenkins",
        "git",
        "ci/cd",
        "terraform",
        "ansible",
        "linux",
        "unix",
        "nginx",
        "apache",
        "prometheus",
        "grafana",
        # Data Science & ML
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "data analysis",
        "data science",
        "nlp",
        "natural language processing",
        "xgboost",
        "lightgbm",
        "spark",
        "hadoop",
        # Tools & Frameworks
        "github",
        "gitlab",
        "bitbucket",
        "jira",
        "confluence",
        "slack",
        "agile",
        "scrum",
        "kanban",
        "figma",
        "sketch",
        "adobe",
        "photoshop",
        "illustrator",
        "postman",
        "swagger",
        "openapi",
        # Testing
        "testing",
        "unit testing",
        "integration testing",
        "test automation",
        "selenium",
        "jest",
        "pytest",
        "junit",
        "cypress",
        # Messaging & Streaming
        "kafka",
        "rabbitmq",
        # Mobile
        "android",
        "ios",
        "react native",
        "flutter",
        "xamarin",
        # Other
        "api",
        "rest",
        "graphql",
        "microservices",
        "devops",
        "tdd",
        "bdd",
        ".net",
        "ux",
        "ui",
        "ui/ux",
        "design",
        "research",
        "analytics",
        "documentation",
        "process mapping",
        "stakeholder management",
        "project management",
        "leadership",
        "mentoring",
        "etl",
        "data engineering",
    }

    SKILL_ALIASES: Dict[str, str] = {
        "nodejs": "node.js",
        "node js": "node.js",
        "reactjs": "react",
        "react js": "react",
        "vuejs": "vue",
        "vue js": "vue",
        "nextjs": "next.js",
        "next js": "next.js",
        "nuxtjs": "nuxt.js",
        "nuxt js": "nuxt.js",
        "svelte kit": "sveltekit",
        "svelte-kit": "sveltekit",
        "c++": "c++",
        "cplusplus": "c++",
        "c plus plus": "c++",
        "c#": "c#",
        "c sharp": "c#",
        "dotnet": ".net",
        "dot net": ".net",
        ".net": ".net",
        "asp net": "asp.net",
        "ci cd": "ci/cd",
        "ci-cd": "ci/cd",
        "ci / cd": "ci/cd",
        "restful": "rest",
        "rest api": "rest",
        "restful api": "rest",
        "postgres": "postgresql",
        "postgre": "postgresql",
        "mongo": "mongodb",
        "k8s": "kubernetes",
        "ml": "machine learning",
        "dl": "deep learning",
        "ai": "artificial intelligence",
        "ui ux": "ui/ux",
        "ux ui": "ui/ux",
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
    }

    DISPLAY_NAMES: Dict[str, str] = {
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "node.js": "Node.js",
        "next.js": "Next.js",
        "nuxt.js": "Nuxt.js",
        "asp.net": "ASP.NET",
        "c++": "C++",
        "c#": "C#",
        ".net": ".NET",
        "ci/cd": "CI/CD",
        "api": "API",
        "rest": "REST",
        "graphql": "GraphQL",
        "ui": "UI",
        "ux": "UX",
        "ui/ux": "UI/UX",
        "html": "HTML",
        "css": "CSS",
        "sql": "SQL",
        "nlp": "NLP",
        "aws": "AWS",
        "gcp": "GCP",
        "qa": "QA",
        "etl": "ETL",
        "ios": "iOS",
        "devops": "DevOps",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "mysql": "MySQL",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "scikit-learn": "scikit-learn",
        "github": "GitHub",
        "gitlab": "GitLab",
        "bitbucket": "Bitbucket",
    }

    ACRONYMS: Set[str] = {
        "api",
        "rest",
        "sql",
        "nlp",
        "ui",
        "ux",
        "qa",
        "aws",
        "gcp",
        "tdd",
        "bdd",
    }

    # Class-level cache
    _known_skill_keys: Optional[Set[str]] = None
    _nlp = None
    _matcher = None

    def __init__(self):
        # Initialize class-level attributes if not done yet
        if SkillExtractor._known_skill_keys is None:
            SkillExtractor._known_skill_keys = set(self.TECHNICAL_SKILLS) | set(
                self.SKILL_ALIASES.keys()
            )

        if spacy and SkillExtractor._nlp is None:
            try:
                SkillExtractor._nlp = spacy.load("en_core_web_sm")
                SkillExtractor._matcher = PhraseMatcher(SkillExtractor._nlp.vocab, attr="LOWER")
                
                # Add all known skills to the matcher
                patterns = [SkillExtractor._nlp.make_doc(text) for text in SkillExtractor._known_skill_keys]
                SkillExtractor._matcher.add("SKILL", patterns)
            except Exception as e:
                logger.error(f"Failed to initialize spaCy: {e}. Ensure en_core_web_sm is downloaded.")
                SkillExtractor._nlp = None

    def extract_skills(
        self, text: str, min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Extract skills from CV text using spaCy.

        Args:
            text: CV text content
            min_confidence: Minimum confidence score to include skill

        Returns:
            List of dictionaries with 'name' and 'confidence_score'
        """
        if not text:
            return []

        found_skills: Dict[str, Dict[str, Any]] = {}

        if SkillExtractor._nlp and SkillExtractor._matcher:
            # Method 1: spaCy PhraseMatcher
            # Truncate text if extremely long to avoid memory issues with NLP
            doc = SkillExtractor._nlp(text[:50000])
            matches = SkillExtractor._matcher(doc)
            
            for match_id, start, end in matches:
                span = doc[start:end]
                skill_key = self.normalize_skill_key(span.text)
                if not skill_key:
                    continue
                    
                if skill_key not in found_skills:
                    found_skills[skill_key] = {
                        "name": self.normalize_skill_name(skill_key),
                        "confidence_score": 0.85, # High confidence for exact spacy matches
                        "count": 0,
                    }
                found_skills[skill_key]["count"] += 1
                
        # Method 2: Context-based extraction (look for skill sections) as fallback/supplement
        skill_sections = self._extract_skill_sections(text)
        for skill in skill_sections:
            skill_key = self.normalize_skill_key(skill)
            if not skill_key:
                continue

            is_known = skill_key in self._known_skill_keys
            base_confidence = 0.9 if is_known else 0.55

            if skill_key not in found_skills:
                found_skills[skill_key] = {
                    "name": self.normalize_skill_name(skill_key),
                    "confidence_score": base_confidence,
                    "count": 1,
                }
            else:
                found_skills[skill_key]["count"] += 1
                found_skills[skill_key]["confidence_score"] = min(
                    1.0, found_skills[skill_key]["confidence_score"] + 0.1
                )

        # Boost confidence for repeated mentions
        for skill_data in found_skills.values():
            if skill_data["count"] > 1:
                boost = min(0.15, 0.05 * (skill_data["count"] - 1))
                skill_data["confidence_score"] = min(
                    1.0, skill_data["confidence_score"] + boost
                )

        # Filter by confidence and return
        result = [
            {
                "name": skill_data["name"],
                "confidence_score": min(1.0, skill_data["confidence_score"]),
            }
            for skill_data in found_skills.values()
            if skill_data["confidence_score"] >= min_confidence
        ]

        result.sort(key=lambda x: x["confidence_score"], reverse=True)
        return result

    def _extract_skill_sections(self, text: str) -> List[str]:
        """Extract skills from dedicated skill sections in CV."""
        skills = []

        # Common section headers
        skill_headers = [
            r"^skills?\s*[:]?\s*$",
            r"^technical\s+skills?\s*[:]?\s*$",
            r"^competencies?\s*[:]?\s*$",
            r"^expertise\s*[:]?\s*$",
            r"^technologies?\s*[:]?\s*$",
            r"^tools?\s*[:]?\s*$",
            r"\bskills?\s*:",
            r"\btechnical\s+skills?\s*:",
        ]

        for header_pattern in skill_headers:
            pattern = re.compile(header_pattern, re.IGNORECASE | re.MULTILINE)
            matches = pattern.finditer(text)

            for match in matches:
                # Extract text after the header (next 500 chars or until next section)
                start_pos = match.end()
                section_text = text[start_pos : start_pos + 500]

                # Extract potential skills (words/phrases separated by commas, semicolons, or newlines)
                skill_items = re.split(r"[,;\n•\|]", section_text)
                for item in skill_items:
                    item = item.strip()
                    if item and len(item) > 2 and len(item) < 50:
                        # Check if it looks like a skill
                        if any(char.isalnum() for char in item):
                            skills.append(item)

        deduped = list(dict.fromkeys(skills))
        return deduped[:25]

    def _extract_compound_skills(self, text: str) -> List[str]:
        """Extract compound skills (multi-word phrases)."""
        compound_patterns = [
            r"machine\s+learning",
            r"deep\s+learning",
            r"artificial\s+intelligence",
            r"natural\s+language\s+processing",
            r"data\s+science",
            r"data\s+analysis",
            r"data\s+engineering",
            r"project\s+management",
            r"stakeholder\s+management",
            r"unit\s+testing",
            r"integration\s+testing",
            r"test\s+automation",
            r"react\s+native",
            r"node\.js",
            r"next\.js",
            r"nuxt\.js",
            r"ci/cd",
            r"ui\s*/\s*ux",
        ]

        found = []
        text_lower = text.lower()
        for pattern in compound_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                found.append(match.group())

        return list(set(found))

    def normalize_skill_key(self, skill: str) -> str:
        """Normalize skill key for matching and de-duplication."""
        if not skill:
            return ""

        if not isinstance(skill, str):
            skill = str(skill)

        key = skill.strip().lower()
        key = key.replace("&", "and")
        key = re.sub(r"[()\[\]{}]", " ", key)
        key = re.sub(r"[_]+", " ", key)
        key = re.sub(r"\s+", " ", key).strip()
        key = key.replace(" / ", "/")

        # Handle cases like "python3" -> "python"
        if key not in self._known_skill_keys:
            # Try stripping version numbers if the skill isn't known
            key_no_version = re.sub(r"\d+(\.\d+)*$", "", key).strip()
            if key_no_version in self._known_skill_keys:
                key = key_no_version

        return self.SKILL_ALIASES.get(key, key)

    def normalize_skill_name(self, skill: str) -> str:
        """Normalize skill name for display."""
        key = self.normalize_skill_key(skill)
        if not key:
            return ""

        display = self.DISPLAY_NAMES.get(key)
        if display:
            return display

        parts = key.split()
        formatted = []
        for part in parts:
            if part in self.ACRONYMS:
                formatted.append(part.upper())
            else:
                formatted.append(part.capitalize())

        return " ".join(formatted)
