# Security Policy

## Supported Versions

Currently, only the `main` branch is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Instead, please report them directly to the project maintainers privately. You can expect an acknowledgment within 48 hours.

Once a vulnerability has been verified and fixed, a public security advisory will be issued.

## Security Best Practices

When contributing to ITAS:
1. Do not hardcode credentials, tokens, or API keys. Use `.env` variables.
2. Ensure you are using parameterized queries or Django ORM correctly to prevent SQL injection.
3. Validate and sanitize all user input before processing.
4. Keep dependencies updated.
