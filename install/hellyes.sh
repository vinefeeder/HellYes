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