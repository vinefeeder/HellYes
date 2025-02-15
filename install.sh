#!/bin/bash

# Detecting installed Chrome browsers
detect_browser() {
    if command -v google-chrome > /dev/null; then
        echo "google-chrome"
    elif command -v chromium > /dev/null; then
        echo "chromium"
    elif command -v brave-browser > /dev/null; then
        echo "brave-browser"
    elif command -v vivaldi > /dev/null; then
        echo "vivaldi"
    else
        echo "No supported browsers found."
        exit 1
    fi
}

# Prompt user for extension ID
read -p "Enter your Chrome Extension ID: " EXTENSION_ID

# Get the current working directory
SCRIPT_DIR="$(pwd)"
NATIVE_SCRIPT_PATH="$SCRIPT_DIR/native.py"

# Define Native Messaging Host JSON
NATIVE_JSON_CONTENT=$(cat <<EOF
{
  "name": "org.hellyes.hellyes",
  "description": "Native messaging",
  "path": "$NATIVE_SCRIPT_PATH",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF
)

# Install the manifest for each detected browser
install_manifest() {
    local browser_name="$1"

    # Determine the correct directory for Native Messaging Hosts
    if [ "$browser_name" == "google-chrome" ]; then
        HOST_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
    elif [ "$browser_name" == "chromium" ]; then
        HOST_DIR="$HOME/.config/chromium/NativeMessagingHosts"
    elif [ "$browser_name" == "brave-browser" ]; then
        HOST_DIR="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
    elif [ "$browser_name" == "vivaldi" ]; then
        HOST_DIR="$HOME/.config/vivaldi/NativeMessagingHosts"
    else
        echo "Unsupported browser: $browser_name"
        exit 1
    fi

    # Create directory if it doesn't exist
    mkdir -p "$HOST_DIR"

    # Save JSON file
    MANIFEST_PATH="$HOST_DIR/org.hellyes.hellyes.json"
    echo "$NATIVE_JSON_CONTENT" > "$MANIFEST_PATH"

    # Set correct permissions
    chmod 644 "$MANIFEST_PATH"

    echo "Installed Native Messaging Host manifest for $browser_name at $MANIFEST_PATH"
}

install_hellyes()
{
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt
}
# Detect installed browser(s) and install manifest
BROWSER=$(detect_browser)
install_manifest "$BROWSER"

echo "Native Messaging Host is set up for $BROWSER."

install_hellyes

echo "✅ Installation complete!"