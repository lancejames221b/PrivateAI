#!/bin/bash
# init_git_repo.sh
# Initialize Git repository for GitHub push

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
echo "║   Private AI 🕵️ - Git Repository Initialization               ║"
echo "║                                                               ║"
echo "║   This script initializes a Git repository and prepares       ║"
echo "║   it for pushing to GitHub.                                   ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Ask for GitHub username
read -p "Enter your GitHub username (default: lancejames221b): " github_username
github_username=${github_username:-lancejames221b}

# Ask for repository name
read -p "Enter the repository name (default: privateAI): " repo_name
repo_name=${repo_name:-privateAI}

# Ask for commit message
read -p "Enter commit message (default: Initial commit: Private AI - AI Tools Privacy Plugin): " commit_message
commit_message=${commit_message:-"Initial commit: Private AI - AI Tools Privacy Plugin"}

# Initialize Git repository
echo -e "${YELLOW}Initializing Git repository...${NC}"
git init

# Add all files
echo -e "${YELLOW}Adding files to Git...${NC}"
git add .

# Commit changes
echo -e "${YELLOW}Committing changes...${NC}"
git commit -m "$commit_message"

# Add remote
echo -e "${YELLOW}Adding remote origin...${NC}"
git remote add origin "https://github.com/$github_username/$repo_name.git"

echo ""
echo -e "${GREEN}✅ Git repository initialized successfully!${NC}"
echo ""
echo -e "${YELLOW}To push to GitHub, run:${NC}"
echo -e "  git push -u origin main"
echo ""
echo -e "${YELLOW}Make sure you have created the repository on GitHub first:${NC}"
echo -e "  https://github.com/new"
echo ""