# Frequently Asked Questions (FAQ)

## General

**Q: What is the primary purpose of ITAS?**
A: ITAS automates the task allocation process for IT projects by matching task requirements against employee skillsets using AI, while keeping track of their historical performance to ensure accurate and unbiased matching.

## Setup & Deployment

**Q: Docker fails to build the backend container due to a package error.**
A: Ensure your Docker base image (`python:3.10-slim` or similar) has the necessary build tools (like `build-essential` or `gcc`) installed before running `pip install -r requirements.txt`. This is specifically needed for some ML libraries.

**Q: The application says "Database connection failed".**
A: If running via Docker, ensure the `db` service is healthy before the `backend` starts. You can configure `depends_on: db: condition: service_healthy` in `docker-compose.yml`.

## Machine Learning & AI

**Q: The AI matching isn't assigning tasks to the right employees.**
A: The ML model weights might need updating. You can force a retrain by running `python -m ai_training.train_model` in the backend repository. Additionally, the system dynamically adjusts scores based on recent performance ratings given by Project Managers.

**Q: CV Parsing returns `None` or fails to extract skills.**
A: Highly graphical CVs, scanned images (without OCR), or encrypted PDFs cannot be parsed accurately. Ensure uploaded CVs are text-based PDFs or DOCX files.

## Contributing

**Q: How do I report a security vulnerability?**
A: Please read our [Security Policy](../SECURITY.md) and do not post vulnerabilities publicly. Contact the maintainers directly.
