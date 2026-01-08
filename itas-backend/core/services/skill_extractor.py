"""
Skill Extraction Service using spaCy and NLTK
Extracts technical skills from CV text using NLP techniques.
"""
import re
import nltk
from typing import List, Set
from collections import Counter

# Download required NLTK data (will be done on first import)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('chunkers/maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker', quiet=True)

try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words', quiet=True)

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk


class SkillExtractor:
    """Service for extracting skills from CV text using NLP."""
    
    # Common technical skills database
    TECHNICAL_SKILLS = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'go', 'rust', 'kotlin',
        'swift', 'php', 'ruby', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell',
        
        # Web Technologies
        'html', 'css', 'react', 'vue', 'angular', 'node.js', 'express', 'django', 'flask',
        'spring', 'laravel', 'asp.net', 'jquery', 'bootstrap', 'sass', 'less', 'webpack',
        
        # Databases
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra',
        'elasticsearch', 'dynamodb', 'neo4j',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'terraform',
        'ansible', 'linux', 'unix', 'nginx', 'apache',
        
        # Data Science & ML
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas',
        'numpy', 'data analysis', 'data science', 'nlp', 'natural language processing',
        
        # Tools & Frameworks
        'git', 'github', 'gitlab', 'jira', 'confluence', 'slack', 'agile', 'scrum', 'kanban',
        'figma', 'sketch', 'adobe', 'photoshop', 'illustrator',
        
        # Testing
        'testing', 'unit testing', 'integration testing', 'selenium', 'jest', 'pytest',
        'junit', 'cypress',
        
        # Mobile
        'android', 'ios', 'react native', 'flutter', 'xamarin',
        
        # Other
        'api', 'rest', 'graphql', 'microservices', 'agile', 'devops', 'ci/cd', 'tdd', 'bdd',
        'ux', 'ui', 'design', 'research', 'analytics', 'documentation', 'process mapping',
        'stakeholder management', 'project management', 'leadership', 'mentoring',
    }
    
    def __init__(self):
        self.skills_pattern = self._build_skills_pattern()
    
    def _build_skills_pattern(self) -> re.Pattern:
        """Build regex pattern for skill matching."""
        # Create pattern that matches skills (case-insensitive, word boundaries)
        skills_list = sorted(self.TECHNICAL_SKILLS, key=len, reverse=True)
        pattern = r'\b(' + '|'.join(re.escape(skill) for skill in skills_list) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def extract_skills(self, text: str, min_confidence: float = 0.3) -> List[dict]:
        """
        Extract skills from CV text.
        
        Args:
            text: CV text content
            min_confidence: Minimum confidence score to include skill
            
        Returns:
            List of dictionaries with 'name' and 'confidence_score'
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = {}
        
        # Method 1: Direct pattern matching
        matches = self.skills_pattern.findall(text_lower)
        for match in matches:
            skill_name = match.lower()
            if skill_name not in found_skills:
                found_skills[skill_name] = {
                    'name': skill_name.title(),
                    'confidence_score': 0.8,  # High confidence for direct matches
                    'count': 0
                }
            found_skills[skill_name]['count'] += 1
        
        # Method 2: Context-based extraction (look for skill sections)
        skill_sections = self._extract_skill_sections(text)
        for skill in skill_sections:
            skill_lower = skill.lower()
            if skill_lower not in found_skills:
                found_skills[skill_lower] = {
                    'name': skill.title(),
                    'confidence_score': 0.9,  # Very high confidence for section-based
                    'count': 1
                }
            else:
                found_skills[skill_lower]['confidence_score'] = min(1.0, 
                    found_skills[skill_lower]['confidence_score'] + 0.1)
        
        # Method 3: N-gram analysis for compound skills
        compound_skills = self._extract_compound_skills(text)
        for skill in compound_skills:
            skill_lower = skill.lower()
            if skill_lower not in found_skills:
                found_skills[skill_lower] = {
                    'name': skill.title(),
                    'confidence_score': 0.6,
                    'count': 1
                }
        
        # Filter by confidence and return
        result = [
            {
                'name': skill_data['name'],
                'confidence_score': min(1.0, skill_data['confidence_score'])
            }
            for skill_data in found_skills.values()
            if skill_data['confidence_score'] >= min_confidence
        ]
        
        # Sort by confidence score
        result.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return result
    
    def _extract_skill_sections(self, text: str) -> List[str]:
        """Extract skills from dedicated skill sections in CV."""
        skills = []
        
        # Common section headers
        skill_headers = [
            r'skills?\s*:',
            r'technical\s+skills?\s*:',
            r'competencies?\s*:',
            r'expertise\s*:',
            r'technologies?\s*:',
            r'tools?\s*:',
        ]
        
        text_lower = text.lower()
        for header_pattern in skill_headers:
            pattern = re.compile(header_pattern, re.IGNORECASE)
            matches = pattern.finditer(text)
            
            for match in matches:
                # Extract text after the header (next 500 chars or until next section)
                start_pos = match.end()
                section_text = text[start_pos:start_pos + 500]
                
                # Extract potential skills (words/phrases separated by commas, semicolons, or newlines)
                skill_items = re.split(r'[,;\n•\-\|]', section_text)
                for item in skill_items:
                    item = item.strip()
                    if item and len(item) > 2 and len(item) < 50:
                        # Check if it looks like a skill
                        if any(char.isalnum() for char in item):
                            skills.append(item)
        
        return skills[:20]  # Limit to top 20
    
    def _extract_compound_skills(self, text: str) -> List[str]:
        """Extract compound skills (multi-word phrases)."""
        compound_patterns = [
            r'machine\s+learning',
            r'deep\s+learning',
            r'natural\s+language\s+processing',
            r'data\s+science',
            r'data\s+analysis',
            r'project\s+management',
            r'stakeholder\s+management',
            r'unit\s+testing',
            r'integration\s+testing',
            r'react\s+native',
            r'node\.js',
            r'ci/cd',
        ]
        
        found = []
        text_lower = text.lower()
        for pattern in compound_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                found.append(match.group())
        
        return list(set(found))
    
    def normalize_skill_name(self, skill: str) -> str:
        """Normalize skill name (capitalize, handle common variations)."""
        skill = skill.strip().title()
        
        # Handle common variations
        variations = {
            'Javascript': 'JavaScript',
            'Typescript': 'TypeScript',
            'C++': 'C++',
            'C#': 'C#',
            'Node.Js': 'Node.js',
            'React Native': 'React Native',
            'Ci/Cd': 'CI/CD',
            'Api': 'API',
            'Rest': 'REST',
            'Graphql': 'GraphQL',
            'Ux': 'UX',
            'Ui': 'UI',
            'Sql': 'SQL',
            'Nlp': 'NLP',
        }
        
        return variations.get(skill, skill)
