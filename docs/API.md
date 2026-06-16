# API Documentation

The Intelligent Task Allocation System (ITAS) provides a comprehensive REST API for managing users, tasks, projects, and machine learning models.

## OpenAPI Specification

We use `drf-spectacular` to automatically generate an OpenAPI 3.0 schema from the backend source code. 

When the development server is running locally, you can access the interactive documentation here:

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **Raw Schema (YAML/JSON)**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

## Authentication

All endpoints under `/api/` (except `/api/auth/login/` and `/api/health/`) require a valid JSON Web Token (JWT). 

Pass the token in the `Authorization` header:
```
Authorization: Bearer <your_token_here>
```

## Available API Versions
- `v1` (Current): All endpoints exposed under `/api/` are currently v1.
