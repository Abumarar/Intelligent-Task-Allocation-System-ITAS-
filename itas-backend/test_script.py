import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itas.settings')
django.setup()

from core.services.skill_extractor import SkillExtractor
from core.services.cv_parser import CVParser

text = """
Name: Mohammad Abumarar
Email: mo.abumarar@gmail.com
Title: Software Engineer

Skills:
React, Python, Leadership, Django
"""
parser = CVParser()
details = parser.extract_details(text)

try:
    extractor = SkillExtractor()
    skills_data = extractor.extract_skills(text)
    details["skills"] = [s["name"] for s in skills_data]
except Exception as e:
    details["skills"] = []
    details["error"] = str(e)

print(details)
