#!/bin/bash
# analyze_copilot_traffic.sh
# Analyze captured GitHub Copilot traffic

# Configuration
LOG_DIR="$HOME/copilot_logs"
ANALYSIS_DIR="$LOG_DIR/analysis"
CAPTURE_FILE="$LOG_DIR/capture.mitm"

# Check if capture file exists
if [ ! -f "$CAPTURE_FILE" ]; then
  echo "Capture file not found at $CAPTURE_FILE"
  echo "Please run launch_vscode_with_proxy.sh first to capture traffic"
  exit 1
fi

# Create analysis directory
mkdir -p "$ANALYSIS_DIR"

# Function to extract specific traffic
extract_traffic() {
  local name=$1
  local filter=$2
  local output_file="$ANALYSIS_DIR/${name}.mitm"
  
  echo "Extracting $name traffic..."
  mitmdump -r "$CAPTURE_FILE" -w "$output_file" "$filter" --listen-port 8082
  
  echo "Saved to $output_file"
}

# Extract different types of traffic
extract_traffic "authentication" "~u /copilot_internal/v2/token"
extract_traffic "models" "~u /models"
extract_traffic "completions" "~u /completions"
extract_traffic "telemetry" "~u /telemetry"

# Convert to HAR format for browser analysis
echo "Converting to HAR format..."
mitmdump -r "$CAPTURE_FILE" --save-stream-file "$ANALYSIS_DIR/capture.har" --listen-port 8082

# Generate summary report
echo "Generating summary report..."
cat > "$ANALYSIS_DIR/summary.md" << EOF
# GitHub Copilot Traffic Analysis

Analysis generated on $(date)

## Traffic Summary

$(mitmdump -r "$CAPTURE_FILE" -n | grep -E "GET|POST|PUT|DELETE" | sort | uniq -c | sort -nr)

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
2. Use mitmproxy to view the full traffic: \`mitmproxy -r "$CAPTURE_FILE"\`
3. Extract specific requests for further analysis
EOF

echo "Analysis complete. Summary report saved to $ANALYSIS_DIR/summary.md"
echo ""
echo "To view the full traffic in mitmproxy:"
echo "  mitmproxy -r \"$CAPTURE_FILE\""
echo ""
echo "To view the summary report:"
echo "  cat \"$ANALYSIS_DIR/summary.md\""