#!/bin/bash
# test_privacy.sh
# Test GitHub Copilot privacy protection with known PII
# This script creates test files with known PII and helps verify that the privacy protection works

# Get the plugin directory
PLUGIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
ROOT_DIR="$( cd "$PLUGIN_DIR/../.." && pwd )"

# Configuration
TEST_DIR="$ROOT_DIR/privacy_test"
SAMPLE_PII_FILE="$TEST_DIR/sample_pii.txt"
TEST_FILES_DIR="$TEST_DIR/test_files"

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
echo "║   Private AI 🕵️ - GitHub Copilot Privacy Test                 ║"
echo "║                                                               ║"
echo "║   This tool creates test files with known PII to verify       ║"
echo "║   that the privacy protection works with GitHub Copilot.      ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Create test directories
mkdir -p "$TEST_DIR"
mkdir -p "$TEST_FILES_DIR"

# Create sample PII file
cat > "$SAMPLE_PII_FILE" << EOF
# Sample PII for Testing

This file contains sample PII that should be detected and transformed by Private AI.

## Personal Information

- Name: John Smith
- Email: john.smith@example.com
- Phone: +1 (555) 123-4567
- SSN: 123-45-6789
- Credit Card: 4111-1111-1111-1111
- Address: 123 Main St, Anytown, CA 94043

## API Keys and Credentials

- API Key: sk_test_abcdefghijklmnopqrstuvwxyz123456
- GitHub Token: ghp_abcdefghijklmnopqrstuvwxyz123456
- AWS Access Key: AKIAIOSFODNN7EXAMPLE
- Database Password: p@ssw0rd123!

## Company Information

- Company: Acme Corporation
- Internal Project: Project Phoenix
- Internal IP: 192.168.1.100
- Server Path: /var/www/internal/acme/config.json
- Database Connection: mongodb://admin:password@db.internal.acme.com:27017/production
EOF

echo -e "${GREEN}✅ Created sample PII file: $SAMPLE_PII_FILE${NC}"

# Create test files with PII for different programming languages
create_test_file() {
  local filename=$1
  local language=$2
  local comment_start=$3
  local comment_end=$4
  
  if [ -z "$comment_end" ]; then
    comment_end=""
  fi
  
  cat > "$TEST_FILES_DIR/$filename" << EOF
$comment_start
This is a test file for GitHub Copilot privacy protection.
It contains PII that should be detected and transformed.

Name: John Smith
Email: john.smith@example.com
API Key: sk_test_abcdefghijklmnopqrstuvwxyz123456
$comment_end

// Function to process user data
function processUserData(userData) {
  // TODO: Implement user data processing
  
}

// Function to authenticate with API
function authenticateWithAPI() {
  const apiKey = "sk_test_abcdefghijklmnopqrstuvwxyz123456";
  const email = "john.smith@example.com";
  
  // TODO: Implement API authentication
}

// Database connection
const dbConfig = {
  host: "db.internal.acme.com",
  user: "admin",
  password: "p@ssw0rd123!",
  database: "production"
};

// User profile
const userProfile = {
  name: "John Smith",
  email: "john.smith@example.com",
  phone: "+1 (555) 123-4567",
  address: "123 Main St, Anytown, CA 94043"
};
EOF

  echo -e "${GREEN}✅ Created test file: $TEST_FILES_DIR/$filename${NC}"
}

# Create test files for different languages
create_test_file "test_javascript.js" "JavaScript" "/*" "*/"
create_test_file "test_python.py" "Python" "#" ""
create_test_file "test_java.java" "Java" "/*" "*/"
create_test_file "test_csharp.cs" "C#" "/*" "*/"
create_test_file "test_typescript.ts" "TypeScript" "/*" "*/"
create_test_file "test_go.go" "Go" "/*" "*/"
create_test_file "test_ruby.rb" "Ruby" "#" ""
create_test_file "test_php.php" "PHP" "/*" "*/"

# Create a test file with prompts to trigger Copilot completions
cat > "$TEST_FILES_DIR/copilot_prompts.js" << EOF
// GitHub Copilot Test Prompts
// These prompts are designed to trigger Copilot completions that might expose PII

// 1. Function to validate email
function validateEmail(email) {
  // TODO: Implement email validation for john.smith@example.com
  
}

// 2. Function to mask credit card
function maskCreditCard(cardNumber) {
  // TODO: Mask credit card number like 4111-1111-1111-1111
  
}

// 3. Function to authenticate with API
function authenticate() {
  // TODO: Use API key sk_test_abcdefghijklmnopqrstuvwxyz123456
  
}

// 4. Function to connect to database
function connectToDatabase() {
  // TODO: Connect to db.internal.acme.com with user admin and password p@ssw0rd123!
  
}

// 5. Function to format user address
function formatAddress(address) {
  // TODO: Format address like 123 Main St, Anytown, CA 94043
  
}

// 6. Function to format phone number
function formatPhoneNumber(phone) {
  // TODO: Format phone number like +1 (555) 123-4567
  
}

// 7. Function to mask SSN
function maskSSN(ssn) {
  // TODO: Mask SSN like 123-45-6789
  
}

// 8. Function to generate AWS config
function generateAWSConfig() {
  // TODO: Generate config with access key AKIAIOSFODNN7EXAMPLE
  
}
EOF

echo -e "${GREEN}✅ Created Copilot prompts file: $TEST_FILES_DIR/copilot_prompts.js${NC}"

# Create a README file with instructions
cat > "$TEST_DIR/README.md" << EOF
# GitHub Copilot Privacy Test

This directory contains test files with known PII to verify that the Private AI privacy protection works with GitHub Copilot.

## How to Use

1. Start the privacy proxy:
   \`\`\`bash
   cd $ROOT_DIR
   ./plugins/copilot_privacy/scripts/launch_vscode_with_privacy.sh
   \`\`\`

2. Open the test files in VS Code:
   \`\`\`bash
   code $TEST_FILES_DIR
   \`\`\`

3. Trigger GitHub Copilot completions by:
   - Placing the cursor after a comment and waiting for suggestions
   - Typing code that might trigger completions related to the PII
   - Using the "Copilot: Generate" command

4. After testing, analyze the captured traffic:
   \`\`\`bash
   cd $ROOT_DIR
   ./plugins/copilot_privacy/scripts/analyze_privacy.sh
   \`\`\`

5. Check the privacy metrics report to verify that PII was detected and transformed.

## Test Files

- \`sample_pii.txt\`: Contains various types of PII for reference
- \`test_*.{js,py,java,cs,ts,go,rb,php}\`: Test files with PII in different programming languages
- \`copilot_prompts.js\`: Contains specific prompts designed to trigger Copilot completions that might expose PII

## Expected Results

When using GitHub Copilot with the privacy proxy:

1. PII in your code should be transformed before being sent to GitHub Copilot
2. Completions should still be relevant and useful
3. The privacy metrics report should show detected and transformed PII

If you see any PII being leaked to GitHub Copilot, please report it as an issue.
EOF

echo -e "${GREEN}✅ Created README file: $TEST_DIR/README.md${NC}"

# Print instructions
echo ""
echo -e "${BLUE}=== Test Setup Complete ===${NC}"
echo ""
echo -e "${YELLOW}To test GitHub Copilot privacy protection:${NC}"
echo ""
echo -e "1. Start the privacy proxy:"
echo -e "   ${GREEN}cd $ROOT_DIR${NC}"
echo -e "   ${GREEN}./plugins/copilot_privacy/scripts/launch_vscode_with_privacy.sh${NC}"
echo ""
echo -e "2. Open the test files in VS Code:"
echo -e "   ${GREEN}code $TEST_FILES_DIR${NC}"
echo ""
echo -e "3. Trigger GitHub Copilot completions in the test files"
echo ""
echo -e "4. After testing, analyze the captured traffic:"
echo -e "   ${GREEN}cd $ROOT_DIR${NC}"
echo -e "   ${GREEN}./plugins/copilot_privacy/scripts/analyze_privacy.sh${NC}"
echo ""
echo -e "5. Check the privacy metrics report to verify that PII was detected and transformed"
echo ""
echo -e "See ${GREEN}$TEST_DIR/README.md${NC} for more detailed instructions."
echo ""