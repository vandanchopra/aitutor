#!/bin/bash

# This script automates running the Khan Academy JSON capture tool.
# It uses mitmdump for stable, non-interactive proxying.

# --- Configuration ---
PROXY_PORT="8080"
PROXY_HOST="127.0.0.1"
CHROME_PROFILE_NAME="Profile 1"
NETWORK_SERVICE="Wi-Fi"

# --- Functions ---
cleanup() {
    echo ""
    echo "[INFO] Cleaning up and restoring network settings..."
    networksetup -setwebproxystate "$NETWORK_SERVICE" off >/dev/null 2>&1
    networksetup -setsecurewebproxystate "$NETWORK_SERVICE" off >/dev/null 2>&1
    echo "[INFO] System proxy for '$NETWORK_SERVICE' has been disabled."
    echo "[INFO] Cleanup complete. Exiting."
    exit 0
}

trap cleanup EXIT

# --- Instructions ---
echo "------------------------------------------------------------------"
echo "Khan Academy Capture Tool"
echo "------------------------------------------------------------------"
echo "[INFO] Using mitmdump for stable, background proxying."
echo "       This terminal will show capture messages as you answer questions."
echo ""
echo "TO STOP: Press Ctrl+C in this terminal window."
echo "------------------------------------------------------------------"
echo ""

# --- Main Execution ---
echo "[INFO] Resetting and setting proxy for '$NETWORK_SERVICE'..."
networksetup -setwebproxystate "$NETWORK_SERVICE" off
networksetup -setsecurewebproxystate "$NETWORK_SERVICE" off
networksetup -setwebproxy "$NETWORK_SERVICE" "$PROXY_HOST" "$PROXY_PORT"
networksetup -setsecurewebproxy "$NETWORK_SERVICE" "$PROXY_HOST" "$PROXY_PORT"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Use mitmdump instead of mitmweb
MITMDUMP_PATH="/Users/vandanchopra/Vandan_Personal_Folder/CODE_STUFF/Projects/venvs/aitutor/bin/mitmdump"

echo "[INFO] Launching Google Chrome..."
open -na "Google Chrome" --args \
    --profile-directory="$CHROME_PROFILE_NAME" \
    --ignore-certificate-errors \
    "https://www.khanacademy.org"

echo "[INFO] Starting proxy in the foreground..."
echo ""

# Run mitmdump. It will load the script once and run until stopped.
"$MITMDUMP_PATH" -q -s capture_khan_json.py --listen-port "$PROXY_PORT"