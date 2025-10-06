# Copilot Instructions for AI Coding Agents

## Project Overview
This repository maintains a clean codebase with automated checks to prevent forbidden files from being committed. It includes GitHub Actions workflows for repository hygiene.

## Repository Hygiene
This project enforces strict repository cleanliness through automated workflows:

- **Clean Repo Check** (`.github/workflows/clean-repo-check.yml`):
  - Runs on every push and pull request
  - Scans for forbidden files: `.DS_Store`, `*.log`, shell histories, cloud storage paths, `.env` files, and Python virtual environments
  - Optionally lints Python code with Black formatter
  - Fails CI if any forbidden files are detected

## File Management Rules
**Never commit these file types:**
- macOS system files (`.DS_Store`)
- Log files (`*.log`) 
- Shell history files (`.zsh_history`, `.bash_history`)
- Environment files (`.env`) - use `.env.example` instead
- Virtual environments (`venv/`, `.venv/`)
- Cloud storage directories (`Library/CloudStorage/*`, `OneDrive-*/*`)
- Trash directories

## Development Workflow
1. Before committing, ensure no forbidden files are present
2. Use `.gitignore` to prevent accidental commits of temporary files
3. Python code should be formatted with Black before committing
4. The clean repo check will catch violations in CI/CD

## Adding New Forbidden Patterns
Update the `find` command in `.github/workflows/clean-repo-check.yml` to add new file patterns that should never be committed.
