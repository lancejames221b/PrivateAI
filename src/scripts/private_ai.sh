#!/bin/bash
# private_ai.sh
# Main script for Private AI tools privacy protection
# This script provides a simple interface to the AI tools privacy plugin

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
echo "║   Private AI 🕵️ - AI Tools Privacy Protection                 ║"
echo "║                                                               ║"
echo "║   This tool provides privacy protection for AI-powered        ║"
echo "║   development tools by intercepting and transforming          ║"
echo "║   sensitive information.                                      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLUGIN_DIR="$SCRIPT_DIR/plugins/ai_tools_privacy"

# Check if the plugin directory exists
if [ ! -d "$PLUGIN_DIR" ]; then
  # Try the old directory name for backward compatibility
  PLUGIN_DIR="$SCRIPT_DIR/plugins/copilot_privacy"
  
  if [ ! -d "$PLUGIN_DIR" ]; then
    echo -e "${RED}❌ AI tools privacy plugin not found at $PLUGIN_DIR${NC}"
    exit 1
  fi
  
  echo -e "${YELLOW}⚠️ Using legacy plugin directory: $PLUGIN_DIR${NC}"
  echo -e "${YELLOW}⚠️ Consider renaming to plugins/ai_tools_privacy for future compatibility${NC}"
fi

# Function to show usage
show_usage() {
  echo -e "${YELLOW}Usage: $0 [command]${NC}"
  echo ""
  echo "Commands:"
  echo "  launch    - Launch VS Code with AI tools privacy protection"
  echo "  analyze   - Analyze captured AI tool traffic"
  echo "  test      - Create test files with known PII"
  echo "  help      - Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 launch   # Launch VS Code with privacy protection"
  echo "  $0 analyze  # Analyze captured traffic"
  echo "  $0 test     # Create test files"
  echo ""
}

# Check if a command was provided
if [ $# -eq 0 ]; then
  show_usage
  exit 0
fi

# Process command
case "$1" in
  launch)
    echo -e "${YELLOW}Launching VS Code with Private AI protection...${NC}"
    "$PLUGIN_DIR/scripts/launch_vscode_with_privacy.sh"
    ;;
  analyze)
    echo -e "${YELLOW}Analyzing captured AI tool traffic...${NC}"
    "$PLUGIN_DIR/scripts/analyze_privacy.sh"
    ;;
  test)
    echo -e "${YELLOW}Creating test files with known PII...${NC}"
    "$PLUGIN_DIR/scripts/test_privacy.sh"
    ;;
  help)
    show_usage
    ;;
  *)
    echo -e "${RED}❌ Unknown command: $1${NC}"
    show_usage
    exit 1
    ;;
esac