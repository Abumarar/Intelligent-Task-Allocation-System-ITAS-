import io

import pytest
from core.services.cv_parser import CVParser
from core.services.skill_extractor import SkillExtractor


def test_extract_details_name():
    text = "Name: John Doe\nEmail: john@example.com\nTitle: Software Engineer"
    details = CVParser.extract_details(text)
    assert details["name"] == "John Doe"
    assert details["email"] == "john@example.com"
    assert details["title"] == "Software Engineer"


def test_extract_details_no_labels():
    text = "Jane Smith\nSoftware Developer\njane@example.com"
    details = CVParser.extract_details(text)
    assert details["email"] == "jane@example.com"
    assert "Jane" in details["name"]


def test_extract_task_details():
    text = "Title: Build API\nDescription: Create REST endpoints\nUrgent priority"
    details = CVParser.extract_task_details(text)
    assert details["title"] == "Build API"
    assert "REST" in details["description"]
    assert details["priority"] == "HIGH"


def test_skill_extractor_normalization():
    extractor = SkillExtractor()
    assert extractor.normalize_skill_key("react.js") == "react.js"
    assert extractor.normalize_skill_key("React JS") == "react"
    assert extractor.normalize_skill_name("node.js") == "Node.js"
    assert extractor.normalize_skill_name("api") == "API"


def test_extract_skills_simple():
    extractor = SkillExtractor()
    text = "Skills: Python, React, AWS, Docker and SQL."
    skills = extractor.extract_skills(text, min_confidence=0.1)
    skill_names = [s["name"].lower() for s in skills]
    assert "python" in skill_names
    assert "react" in skill_names
    assert "aws" in skill_names
    assert "sql" in skill_names
