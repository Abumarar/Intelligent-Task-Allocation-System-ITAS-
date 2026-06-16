# Contributing to ITAS

First off, thank you for considering contributing to the Intelligent Task Allocation System (ITAS). It's people like you that make ITAS such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

- Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/Abumarar/Intelligent-Task-Allocation-System-ITAS-/issues).
- If you're unable to find an open issue addressing the problem, open a new one. Be sure to include a title and clear description, as much relevant information as possible, and a code sample or an executable test case demonstrating the expected behavior that is not occurring.
- Use the Bug Report issue template.

### Suggesting Enhancements

- Open a new issue with the Feature Request template.
- Provide a clear and detailed explanation of the feature.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes (`pytest` for backend, `vitest` for frontend).
5. Make sure your code lints (Black/Flake8 for Python, ESLint/Prettier for TS).
6. Issue that pull request!

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Consider using Conventional Commits format (e.g., `feat: add new API endpoint`)

### Python Styleguide

- All Python code should be formatted with `black`.
- Imports should be sorted with `isort`.

### TypeScript/React Styleguide

- All TS code should be formatted with `prettier`.
- Ensure there are no ESLint warnings or errors before committing.
