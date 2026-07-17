# Contributing to MindGuard

Thank you for your interest in contributing. All contributions are welcomed: bug reports, feature suggestions, documentation improvements, and pull requests.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Message Convention](#commit-message-convention)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this standard.

---

## Reporting Bugs

Before opening a new issue, please search existing issues to avoid duplicates.

When reporting a bug, include:

- **Environment:** OS, Python version, Node.js version
- **Steps to reproduce:** The minimal sequence of actions that triggers the bug
- **Expected behavior:** What you expected to happen
- **Actual behavior:** What actually happened
- **Logs:** Relevant stack traces or log output

---

## Suggesting Features

Open a GitHub Issue with the label `enhancement` and describe:

- The problem you are trying to solve
- Your proposed solution
- Any alternatives you considered

---

## Development Setup

See the [Developer Guide](docs/developer/DEVELOPER_GUIDE.md) for step-by-step local environment setup.

---

## Pull Request Process

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** following the coding standards below.

3. **Write or update tests** for any changed behavior.

4. **Ensure all tests pass:**
   ```bash
   pytest backend/tests/
   cd frontend && npx tsc --noEmit && npm run test
   ```

5. **Lint your code:**
   ```bash
   ruff check backend/ tracker/
   cd frontend && npm run lint
   ```

6. **Open a Pull Request** against the `main` branch. Complete the PR template, linking any related issues.

7. Your PR will be reviewed within a few business days. Please respond to feedback promptly.

---

## Coding Standards

| Language | Formatter | Linter |
|:---|:---|:---|
| Python | `ruff format` | `ruff check` |
| TypeScript / TSX | `prettier` | `eslint` |

---

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Examples:**
```
feat(api): add batch behaviour ingestion endpoint
fix(tracker): resolve exponential backoff race condition
docs(api): update WebSocket authentication flow
refactor(ml): extract SHAP explainer into dedicated module
```
