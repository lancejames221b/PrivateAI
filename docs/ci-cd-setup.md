# CI/CD Setup for Private AI Proxy

This document describes the Continuous Integration and Continuous Deployment (CI/CD) setup for the Private AI Proxy project.

## Overview

The CI/CD pipeline is implemented using GitHub Actions and consists of three main workflows:

1. **CI Workflow** - Runs tests and code coverage
2. **PR Checks Workflow** - Performs automated builds and testing for pull requests
3. **Deployment Workflow** - Handles automated deployment for releases

## CI Workflow

The CI workflow (`ci.yml`) runs on pushes to the main branch and on pull requests. It performs the following tasks:

- Sets up Python environments (3.8 and 3.9)
- Installs project dependencies
- Runs tests with code coverage
- Uploads coverage reports to Codecov

This workflow ensures that the codebase remains functional and that test coverage is maintained.

## PR Checks Workflow

The PR Checks workflow (`pr-checks.yml`) runs on pull requests to the main branch. It performs the following tasks:

- Lints the code with flake8
- Checks code formatting with black
- Checks import ordering with isort
- Builds Docker images
- Verifies that the Docker images can run successfully

This workflow helps maintain code quality and ensures that pull requests meet the project's standards before they are merged.

## Deployment Workflow

The Deployment workflow (`deploy.yml`) runs when a new release is published or manually triggered. It performs the following tasks:

- Builds Docker images for the application
- Pushes the images to GitHub Container Registry
- Deploys the application to the specified environment (staging or production)

This workflow automates the deployment process, making it easier to release new versions of the application.

## Code Coverage

Code coverage is configured using pytest-cov and the `.coveragerc` file. The coverage reports are generated in XML format and uploaded to Codecov for visualization and tracking.

## Local Development

To run the tests and generate coverage reports locally, you can use the following commands:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage
pytest --cov=.

# Generate HTML coverage report
pytest --cov=. --cov-report=html
```

## CI/CD Pipeline Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Code Push  │────▶│ Run Tests & │────▶│  Coverage   │
│  or PR      │     │ Linting     │     │  Reports    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Release    │────▶│ Build Docker│────▶│  Deploy to  │
│  Published  │     │   Images    │     │ Environment │
└─────────────┘     └─────────────┘     └─────────────┘