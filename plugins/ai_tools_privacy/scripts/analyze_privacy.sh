#!/bin/bash
# analyze_privacy.sh
# Analyze captured GitHub Copilot traffic with privacy metrics
# This script analyzes the traffic captured by the Private AI proxy and shows PII protection metrics

# Get the plugin directory
PLUGIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
ROOT_DIR="$( cd "$PLUGIN_DIR/../.." && pwd )"

# Configuration
LOG_DIR="$ROOT_DIR/proxy_logs"
ANALYSIS_DIR="$LOG_DIR/analysis"
LATEST_CAPTURE=$(ls -t "$LOG_DIR"/capture_*.mitm 2>/dev/null | head -1)
LATEST_LOG=$(ls -t "$LOG_DIR"/proxy_log_*.txt 2>/dev/null | head -1)

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
echo "║   Private AI 🕵️ - GitHub Copilot Privacy Analysis             ║"
echo "║                                                               ║"
echo "║   This tool analyzes captured GitHub Copilot traffic and      ║"
echo "║   provides metrics on PII detection and transformation.       ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if capture file exists
if [ -z "$LATEST_CAPTURE" ]; then
  echo -e "${RED}❌ No capture file found in $LOG_DIR${NC}"
  echo -e "${YELLOW}Please run launch_vscode_with_privacy.sh first to capture traffic${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Using capture file: $LATEST_CAPTURE${NC}"

# Check if log file exists
if [ -z "$LATEST_LOG" ]; then
  echo -e "${YELLOW}⚠️ No log file found in $LOG_DIR${NC}"
  echo -e "${YELLOW}PII transformation metrics will not be available${NC}"
else
  echo -e "${GREEN}✅ Using log file: $LATEST_LOG${NC}"
fi

# Create analysis directory
mkdir -p "$ANALYSIS_DIR"

# Function to extract specific traffic
extract_traffic() {
  local name=$1
  local filter=$2
  local output_file="$ANALYSIS_DIR/${name}.mitm"
  
  echo -e "${YELLOW}Extracting $name traffic...${NC}"
  mitmdump -r "$LATEST_CAPTURE" -w "$output_file" "$filter" --listen-port 8082
  
  echo -e "${GREEN}✅ Saved to $output_file${NC}"
}

# Extract different types of traffic
extract_traffic "authentication" "~u /copilot_internal/v2/token"
extract_traffic "models" "~u /models"
extract_traffic "completions" "~u /completions"
extract_traffic "telemetry" "~u /telemetry"

# Convert to HAR format for browser analysis
echo -e "${YELLOW}Converting to HAR format...${NC}"
mitmdump -r "$LATEST_CAPTURE" --save-stream-file "$ANALYSIS_DIR/capture.har" --listen-port 8082
echo -e "${GREEN}✅ Saved to $ANALYSIS_DIR/capture.har${NC}"

# Analyze PII transformations from log file
if [ -n "$LATEST_LOG" ]; then
  echo -e "${YELLOW}Analyzing PII transformations...${NC}"
  
  # Count total requests and responses
  TOTAL_REQUESTS=$(grep -c "Processing Copilot request" "$LATEST_LOG")
  TOTAL_RESPONSES=$(grep -c "Processing Copilot response" "$LATEST_LOG")
  
  # Count transformed requests and responses
  TRANSFORMED_REQUESTS=$(grep -c "Successfully transformed Copilot request" "$LATEST_LOG")
  TRANSFORMED_RESPONSES=$(grep -c "Successfully transformed Copilot response" "$LATEST_LOG")
  
  # Count PII detections
  PII_DETECTED=$(grep -c "Detected and transformed .* instances of PII" "$LATEST_LOG")
  
  # Extract PII types that were transformed
  PII_TYPES=$(grep -o "REDACTED-[A-Z_]+-[a-f0-9]+" "$LATEST_LOG" | sort | uniq -c | sort -nr)
  
  # Generate privacy metrics report
  PRIVACY_REPORT="$ANALYSIS_DIR/privacy_metrics.md"
  
  cat > "$PRIVACY_REPORT" << EOF
# GitHub Copilot Privacy Protection Metrics

Analysis generated on $(date)

## Traffic Summary

- Total Requests: $TOTAL_REQUESTS
- Total Responses: $TOTAL_RESPONSES
- Transformed Requests: $TRANSFORMED_REQUESTS
- Transformed Responses: $TRANSFORMED_RESPONSES
- PII Detections: $PII_DETECTED

## Format Detection

- GitHub Copilot Requests: $TOTAL_REQUESTS
- GitHub Copilot Responses: $TOTAL_RESPONSES

## PII Protection

The following types of PII were detected and transformed:

\`\`\`
$PII_TYPES
\`\`\`

## Privacy Effectiveness

- Request Protection Rate: $(( TRANSFORMED_REQUESTS * 100 / (TOTAL_REQUESTS > 0 ? TOTAL_REQUESTS : 1) ))%
- Response Protection Rate: $(( TRANSFORMED_RESPONSES * 100 / (TOTAL_RESPONSES > 0 ? TOTAL_RESPONSES : 1) ))%

## Log Excerpts

### PII Transformations

\`\`\`
$(grep "transform_text" "$LATEST_LOG" | head -10)
\`\`\`

### Format Adaptations

\`\`\`
$(grep "Detected and transformed" "$LATEST_LOG" | head -10)
\`\`\`
EOF

  echo -e "${GREEN}✅ Privacy metrics report generated: $PRIVACY_REPORT${NC}"
fi

# Generate traffic summary report
echo -e "${YELLOW}Generating traffic summary report...${NC}"
SUMMARY_REPORT="$ANALYSIS_DIR/traffic_summary.md"

cat > "$SUMMARY_REPORT" << EOF
# GitHub Copilot Traffic Analysis

Analysis generated on $(date)

## Traffic Summary

$(mitmdump -r "$LATEST_CAPTURE" -n | grep -E "GET|POST|PUT|DELETE" | sort | uniq -c | sort -nr)

## Authentication Requests

$(mitmdump -r "$ANALYSIS_DIR/authentication.mitm" -n | grep -E "GET|POST|PUT|DELETE")

## Model Requests

$(mitmdump -r "$ANALYSIS_DIR/models.mitm" -n | grep -E "GET|POST|PUT|DELETE")

## Completion Requests

$(mitmdump -r "$ANALYSIS_DIR/completions.mitm" -n | grep -E "GET|POST|PUT|DELETE")

## Telemetry Requests

$(mitmdump -r "$ANALYSIS_DIR/telemetry.mitm" -n | grep -E "GET|POST|PUT|DELETE")

## Next Steps

1. Open the HAR file in a browser developer tools to inspect detailed request/response data
2. Use mitmproxy to view the full traffic: \`mitmproxy -r "$LATEST_CAPTURE"\`
3. Review the privacy metrics report for PII protection statistics
EOF

echo -e "${GREEN}✅ Traffic summary report generated: $SUMMARY_REPORT${NC}"

# Print summary
echo ""
echo -e "${BLUE}=== Analysis Complete ===${NC}"
echo ""
echo -e "${YELLOW}To view the traffic summary report:${NC}"
echo -e "  cat \"$SUMMARY_REPORT\""
echo ""
if [ -n "$LATEST_LOG" ]; then
  echo -e "${YELLOW}To view the privacy metrics report:${NC}"
  echo -e "  cat \"$PRIVACY_REPORT\""
  echo ""
fi
echo -e "${YELLOW}To view the full traffic in mitmproxy:${NC}"
echo -e "  mitmproxy -r \"$LATEST_CAPTURE\""
echo ""
echo -e "${YELLOW}To view the HAR file in a browser:${NC}"
echo -e "  Open \"$ANALYSIS_DIR/capture.har\" in a browser's developer tools"
echo ""