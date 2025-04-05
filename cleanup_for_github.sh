#!/bin/bash
# cleanup_for_github.sh
# Clean up unnecessary files before GitHub push

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
echo "║   Private AI 🕵️ - Cleanup for GitHub                          ║"
echo "║                                                               ║"
echo "║   This script cleans up unnecessary files before pushing      ║"
echo "║   to GitHub, ensuring only essential files are included.      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Files to remove
FILES_TO_REMOVE=(
  # Old scripts
  "analyze_copilot_traffic.sh"
  "launch_vscode_with_proxy.sh"
  "reset_vscode_direct.sh"
  "install_mitmproxy_cert.sh"
  "COPILOT_TRAFFIC_CAPTURE_README.md"
  "analyze_copilot_privacy.sh"
  "launch_vscode_with_privacy_proxy.sh"
  "test_copilot_privacy.sh"
  "GITHUB_COPILOT_PRIVACY_INTEGRATION.md"
  "cleanup_old_scripts.sh"
  "cleanup_remaining_files.sh"
  "copilot_privacy.sh"
  "COPILOT_PRIVACY_README.md"
  
  # Temporary files
  "*.tmp"
  "*.bak"
  "*.swp"
  "*.swo"
  
  # Log files
  "*.log"
  
  # Certificate files
  "*.pem"
  "*.crt"
  "*.key"
)

# Directories to remove
DIRS_TO_REMOVE=(
  "old_scripts_backup"
  "logs"
  "proxy_logs"
  "__pycache__"
  ".pytest_cache"
)

# Create backup directory
BACKUP_DIR="./pre_github_backup"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✅ Created backup directory: $BACKUP_DIR${NC}"

# Backup and remove files
for file in "${FILES_TO_REMOVE[@]}"; do
  # Handle wildcards
  if [[ "$file" == *"*"* ]]; then
    # Use find to get all matching files
    matching_files=$(find . -name "$file" -type f -not -path "./pre_github_backup/*" -not -path "./.git/*")
    for matching_file in $matching_files; do
      echo -e "${YELLOW}Backing up $matching_file to $BACKUP_DIR/${matching_file//\//_}${NC}"
      cp "$matching_file" "$BACKUP_DIR/${matching_file//\//_}"
      echo -e "${YELLOW}Removing $matching_file${NC}"
      rm "$matching_file"
      echo -e "${GREEN}✅ Removed $matching_file${NC}"
    done
  else
    # Handle specific files
    if [ -f "$file" ]; then
      echo -e "${YELLOW}Backing up $file to $BACKUP_DIR/${file//\//_}${NC}"
      cp "$file" "$BACKUP_DIR/${file//\//_}"
      echo -e "${YELLOW}Removing $file${NC}"
      rm "$file"
      echo -e "${GREEN}✅ Removed $file${NC}"
    fi
  fi
done

# Backup and remove directories
for dir in "${DIRS_TO_REMOVE[@]}"; do
  if [ -d "$dir" ]; then
    echo -e "${YELLOW}Backing up $dir to $BACKUP_DIR/${dir//\//_}${NC}"
    cp -r "$dir" "$BACKUP_DIR/${dir//\//_}"
    echo -e "${YELLOW}Removing $dir${NC}"
    rm -rf "$dir"
    echo -e "${GREEN}✅ Removed $dir${NC}"
  fi
done

# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p proxy_logs

# Rename plugin directory if needed
if [ -d "plugins/copilot_privacy" ] && [ ! -d "plugins/ai_tools_privacy" ]; then
  echo -e "${YELLOW}Renaming plugins/copilot_privacy to plugins/ai_tools_privacy...${NC}"
  mkdir -p "plugins/ai_tools_privacy"
  cp -r "plugins/copilot_privacy/"* "plugins/ai_tools_privacy/"
  rm -rf "plugins/copilot_privacy"
  echo -e "${GREEN}✅ Renamed plugin directory${NC}"
fi

echo ""
echo -e "${BLUE}=== Cleanup Complete ===${NC}"
echo ""
echo -e "${GREEN}Unnecessary files have been backed up to $BACKUP_DIR and removed.${NC}"
echo -e "${GREEN}The repository is now ready for GitHub push.${NC}"
echo ""
echo -e "${YELLOW}To initialize the Git repository and push to GitHub:${NC}"
echo -e "  git init"
echo -e "  git add ."
echo -e "  git commit -m \"Initial commit: Private AI - AI Tools Privacy Plugin\""
echo -e "  git remote add origin https://github.com/yourusername/private-ai.git"
echo -e "  git push -u origin main"
echo ""