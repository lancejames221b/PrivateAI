# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Run Commands
- Install dependencies: `python -m pip install -r requirements.txt`
- Run proxy server: `./run_proxy.sh` or `python3 ai_proxy.py`
- Run MITM proxy: `./run_mitm_proxy.sh` or `./run_proxy.sh --mitm`
- Run admin panel: `./run_admin.sh` (runs app.py - accessible at http://localhost:5000)
- Setup certificates: `./setup_certificates.sh` (for MITM proxy)

## Test Commands
- Run privacy assistant test: `python test_privacy_assistant.py`
- Run PII transformation test: `python test_transform.py`
- Run proxy test: `python test_proxy.py [--proxy URL] [--api ENDPOINT] [--no-sensitive]`

## Code Style Guidelines
- Follow PEP 8 conventions for Python code
- Use docstrings to document modules and functions
- Organize imports: stdlib first, then third-party, then local modules
- Maximum line length: 100 characters
- Use 4 spaces for indentation
- Use clear, descriptive variable names (snake_case for variables and functions)
- Prefer explicit error handling with try/except blocks
- Validate user input and API responses