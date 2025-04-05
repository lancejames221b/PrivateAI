#!/bin/bash
# reorganize_repo.sh
# Script to reorganize the repository structure

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   Private AI 🕵️ - Repository Reorganization                   ║"
echo "║                                                               ║"
echo "║   This script reorganizes the repository structure to         ║"
echo "║   make it cleaner and more maintainable.                      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Create directories if they don't exist
mkdir -p src/core
mkdir -p src/proxy
mkdir -p src/privacy
mkdir -p src/utils
mkdir -p src/plugins
mkdir -p src/scripts
mkdir -p src/tests
mkdir -p src/examples
mkdir -p src/web
mkdir -p src/config

# Move core Python files to src/core
echo -e "${YELLOW}Moving core Python files to src/core...${NC}"
mv ai_format_adapter.py src/core/
mv ai_format_detector.py src/core/
mv ai_format_request_adapters.py src/core/
mv ai_format_response_adapters.py src/core/
mv ai_proxy.py src/core/
mv app.py src/core/
mv codename_generator.py src/core/
mv db_setup.py src/core/
mv pii_transform.py src/core/
mv privacy_assistant.py src/core/
mv transformers_recognizer.py src/core/
mv utils.py src/core/

# Move proxy-related files to src/proxy
echo -e "${YELLOW}Moving proxy-related files to src/proxy...${NC}"
mv proxy_base.py src/proxy/
mv proxy_intercept.py src/proxy/
mv proxy_script.py src/proxy/
mv setup_proxy.py src/proxy/
mv copilot_proxy.py src/proxy/
mv simple_copilot_proxy.py src/proxy/
mv simple_proxy.py src/proxy/
mv trusted_proxy.py src/proxy/
mv certificate_manager.py src/proxy/
mv setup_certificates.py src/proxy/

# Move test files to src/tests
echo -e "${YELLOW}Moving test files to src/tests...${NC}"
mv test_*.py src/tests/
mv tests/* src/tests/
rmdir tests

# Move scripts to src/scripts
echo -e "${YELLOW}Moving scripts to src/scripts...${NC}"
mv *.sh src/scripts/
mv scripts/* src/scripts/
rmdir scripts

# Move JavaScript files to src/web
echo -e "${YELLOW}Moving JavaScript files to src/web...${NC}"
mv *.js src/web/

# Move plugins to src/plugins
echo -e "${YELLOW}Moving plugins to src/plugins...${NC}"
cp -r plugins/* src/plugins/
rm -rf plugins

# Move examples to src/examples
echo -e "${YELLOW}Moving examples to src/examples...${NC}"
cp -r examples/* src/examples/
rm -rf examples

# Move static and templates to src/web
echo -e "${YELLOW}Moving web files to src/web...${NC}"
cp -r static src/web/
cp -r templates src/web/
rm -rf static
rm -rf templates

# Create a new main.py in the root directory
echo -e "${YELLOW}Creating main.py in the root directory...${NC}"
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Private AI - Main entry point

This is the main entry point for the Private AI application.
It provides a simple interface to the various components.
"""

import os
import sys
import argparse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point for the Private AI application."""
    parser = argparse.ArgumentParser(description='Private AI - AI Tools Privacy Protection')
    parser.add_argument('command', choices=['launch', 'analyze', 'test', 'help'],
                        help='Command to execute')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.command == 'launch':
        from core.ai_proxy import launch_proxy
        launch_proxy(debug=args.debug)
    elif args.command == 'analyze':
        from privacy.analyzer import analyze_traffic
        analyze_traffic(debug=args.debug)
    elif args.command == 'test':
        from tests.test_privacy import run_tests
        run_tests(debug=args.debug)
    elif args.command == 'help':
        parser.print_help()

if __name__ == '__main__':
    main()
EOF
chmod +x main.py

# Create a new setup.py in the root directory
echo -e "${YELLOW}Creating setup.py in the root directory...${NC}"
cat > setup.py << 'EOF'
#!/usr/bin/env python3
"""
Private AI - Setup script

This script installs the Private AI package.
"""

from setuptools import setup, find_packages

setup(
    name="privateai",
    version="1.0.0",
    author="Lance James",
    author_email="lance@unit221b.com",
    description="Privacy protection for AI-powered development tools",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/lancejames221b/PrivateAI",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "privateai=main:main",
        ],
    },
)
EOF

# Create a new .gitignore in the root directory
echo -e "${YELLOW}Updating .gitignore in the root directory...${NC}"
cat > .gitignore << 'EOF'
# Python bytecode
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Virtual environments
venv/
env/
ENV/
privacy_proxy_env/

# Testing
.pytest_cache/
.coverage
coverage.xml

# Logs and data
logs/
proxy_logs/
*.log
data/

# Certificates
*.pem
*.crt
*.key

# Environment variables
.env
.env.*
!.env.example

# Backup files
old_scripts_backup/
*.bak
*~

# macOS
.DS_Store

# VS Code
.vscode/
*.code-workspace

# Temporary files
*.tmp
*.swp
*.swo

# Docker
.dockerignore

# Specific project files
transformer_diagnostics.json
fetchfailure.txt

# API keys and sensitive information
keys.txt
EOF

# Update README.md with new structure
echo -e "${YELLOW}Updating README.md with new structure...${NC}"
sed -i '' 's/```\n\..*```/```\n.\n├── main.py                  # Main entry point\n├── setup.py                # Package setup script\n├── README.md                # This file\n├── LICENSE                  # MIT License\n├── requirements.txt         # Python dependencies\n└── src/                    # Source code\n    ├── core/               # Core functionality\n    ├── proxy/              # Proxy implementation\n    ├── privacy/            # Privacy protection\n    ├── utils/              # Utility functions\n    ├── plugins/            # Plugin system\n    ├── scripts/            # Shell scripts\n    ├── tests/              # Test suite\n    ├── examples/           # Example code\n    └── web/                # Web interface\n```/g' README.md

echo ""
echo -e "${GREEN}✅ Repository structure reorganized successfully!${NC}"
echo ""
echo -e "${YELLOW}To commit and push the changes:${NC}"
echo -e "  git add ."
echo -e "  git commit -m \"Reorganize repository structure\""
echo -e "  git push -f origin main"
echo ""