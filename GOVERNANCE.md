# ITAS Governance Model

## Roles and Responsibilities

### Maintainers
Maintainers are responsible for the overall health of the project, merging pull requests, and making final decisions on architectural changes.

### Contributors
Anyone who submits a pull request, opens an issue, or helps with documentation is a contributor.

## Decision Making Process
Major decisions (architectural changes, dropping support for older versions) require an RFC (Request for Comments) issue to be opened and discussed for at least 7 days. If there's no consensus, maintainers have the final say.

## Branch Protection
The `main` branch is protected. 
- All changes must go through a Pull Request.
- At least 1 approving review is required.
- CI/CD checks (backend tests, frontend tests, linting) must pass before merging.

## Release Process and Versioning
We use [Semantic Versioning](https://semver.org/).
- `MAJOR` version when making incompatible API changes,
- `MINOR` version when adding functionality in a backwards compatible manner, and
- `PATCH` version when making backwards compatible bug fixes.

Releases are tagged via GitHub releases.

## Deprecation Policy
Before a feature or API is removed, it must be marked as deprecated for at least one minor release cycle.
