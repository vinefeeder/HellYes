#!/bin/bash

# Check if a browser is installed via snap
is_snap_installed() {
    local browser_name="$1"
    local browser_path
    browser_path=$(command -v "$browser_name")
    if [[ "$browser_path" == *"/snap/"* ]]; then
         return 0
    else
         return 1
    fi
}

# Detect installed Chrome‑based browsers (can be multiple)
detect_chrome_browsers() {
    local browsers=()
    if command -v google-chrome > /dev/null; then
        browsers+=("google-chrome")
    fi
    if command -v chromium > /dev/null; then
        browsers+=("chromium")
    fi
    if command -v brave-browser > /dev/null; then
        browsers+=("brave-browser")
    fi
    if command -v vivaldi > /dev/null; then
        browsers+=("vivaldi")
    fi

    if [ ${#browsers[@]} -eq 0 ]; then
        echo "none"
    else
        echo "${browsers[@]}"
    fi
}

# Detect installed Firefox
detect_firefox() {
    if command -v firefox > /dev/null; then
        echo "firefox"
    else
        echo "none"
    fi
}

# Get the current working directory and native script path
SCRIPT_DIR="$(pwd)"
NATIVE_SCRIPT_PATH="$SCRIPT_DIR/native.py"

# Build the JSON manifest for Chrome‑based browsers
build_chrome_manifest() {
    local extension_id="$1"
    cat <<EOF
{
  "name": "org.hellyes.hellyes",
  "description": "Native messaging",
  "path": "$NATIVE_SCRIPT_PATH",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$extension_id/"
  ]
}
EOF
}

# Build the JSON manifest for Firefox
build_firefox_manifest() {
    cat <<EOF
{
  "name": "org.hellyes.hellyes",
  "description": "Native messaging",
  "path": "$NATIVE_SCRIPT_PATH",
  "type": "stdio",
  "allowed_extensions": [
    "hellyes@hellyes.org"
  ]
}
EOF
}

# Install manifest for a given Chrome‑based browser
install_manifest_chrome() {
    local browser_name="$1"
    local EXTENSION_ID="$2"
    local HOST_DIR=""

    if [ "$browser_name" == "google-chrome" ]; then
        HOST_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
    elif [ "$browser_name" == "chromium" ]; then
        HOST_DIR="$HOME/.config/chromium/NativeMessagingHosts"
    elif [ "$browser_name" == "brave-browser" ]; then
        HOST_DIR="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
    elif [ "$browser_name" == "vivaldi" ]; then
        HOST_DIR="$HOME/.config/vivaldi/NativeMessagingHosts"
    else
        echo "Unsupported chrome browser: $browser_name"
        return 1
    fi

    mkdir -p "$HOST_DIR"
    local MANIFEST_PATH="$HOST_DIR/org.hellyes.hellyes.json"
    local manifest_content
    manifest_content=$(build_chrome_manifest "$EXTENSION_ID")
    echo "$manifest_content" > "$MANIFEST_PATH"
    chmod 644 "$MANIFEST_PATH"
    echo "Installed Native Messaging Host manifest for $browser_name at $MANIFEST_PATH"
}

# Install manifest for Firefox
install_manifest_firefox() {
    local HOST_DIR="$HOME/.mozilla/native-messaging-hosts"
    mkdir -p "$HOST_DIR"
    local MANIFEST_PATH="$HOST_DIR/org.hellyes.hellyes.json"
    local manifest_content
    manifest_content=$(build_firefox_manifest)
    echo "$manifest_content" > "$MANIFEST_PATH"
    chmod 644 "$MANIFEST_PATH"
    echo "Installed Native Messaging Host manifest for firefox at $MANIFEST_PATH"
}

# Install the Python environment and dependencies stealthily with a spinner.
install_hellyes() {
    echo "Installing Python environment and dependencies..."
    # Create virtual environment quietly
    python3 -m venv venv > /dev/null 2>&1
    if [ $? -ne 0 ]; then
         echo "Error: Could not create virtual environment."
         python3 -m venv venv
         exit 1
    fi

    # Install dependencies quietly with a progress spinner.
    TEMP_LOG=$(mktemp)
    (./venv/bin/pip install -r requirements.txt > "$TEMP_LOG" 2>&1) &
    PID=$!

    spinner() {
      local pid=$1
      local delay=0.1
      local spinstr='|/-\'
      while kill -0 "$pid" 2>/dev/null; do
          for (( i=0; i<${#spinstr}; i++ )); do
              printf "\rInstalling dependencies... [${spinstr:$i:1}]"
              sleep $delay
          done
      done
      printf "\rInstalling dependencies... Done!\n"
    }

    spinner $PID
    wait $PID
    EXIT_STATUS=$?
    if [ $EXIT_STATUS -ne 0 ]; then
         echo "Error installing Python dependencies:"
         cat "$TEMP_LOG"
         rm "$TEMP_LOG"
         exit $EXIT_STATUS
    fi
    rm "$TEMP_LOG"
}

# --- Main Installation ---

# Install Python environment first
install_hellyes

# Install for Chrome‑based browsers if any are detected
chrome_browsers=$(detect_chrome_browsers)
if [ "$chrome_browsers" != "none" ]; then
    read -p "Enter your Chrome Extension ID: " EXTENSION_ID
    for browser in $chrome_browsers; do
        if is_snap_installed "$browser"; then
            echo -e "\033[0;31m⚠️ Warning: $browser appears to be installed via snap. Native messaging may not work with snap-based installations. ⚠️\033[0m"
        fi
        install_manifest_chrome "$browser" "$EXTENSION_ID"
    done
    echo "✅ Native Messaging Host is set up for Chrome‑based browsers: $chrome_browsers."
fi

# Install for Firefox if it is detected
firefox_browser=$(detect_firefox)
if [ "$firefox_browser" != "none" ]; then
    if is_snap_installed "firefox"; then
        echo -e "\033[0;31m⚠️ Warning: firefox appears to be installed via snap. Native messaging may not work with snap-based installations. ⚠️\033[0m"
    fi
    install_manifest_firefox
    echo "✅ Native Messaging Host is set up for Firefox."
fi

echo "✅ Installation complete!"
