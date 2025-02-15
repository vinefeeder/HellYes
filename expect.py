#!/usr/bin/env venv/bin/python3
import pexpect
import sys
import time

class LogWrapper:
    def write(self, data):
        # Convert bytes to string if necessary
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='replace')
        sys.stdout.write(data)
        sys.stdout.flush()

    def flush(self):
        sys.stdout.flush()

# Read the MPD URL from file.
with open("manifestUrl.txt", "r", encoding="utf-8") as f:
    mpd_url = f.read().strip()

# Read the cURL input from file.
with open("cUrl.txt", "r", encoding="utf-8") as f:
    curl_input = f.read()

# Define a video name
with open("title.txt", "r", encoding="utf-8") as f:
    video_title = f.read()

# Spawn the original script using your virtual environment’s Python.
child = pexpect.spawn(
    "./venv/bin/python3 ./allhell3.py",
    encoding="utf-8",
    timeout=30
)

# Set the logfile to our custom wrapper so that we see all output.
child.logfile = LogWrapper()

# Wait for the MPD URL prompt and send the MPD URL.
child.expect("MPD URL\\? ")
child.sendline(mpd_url)

# Wait for the cURL prompt.
child.expect("cURL\\? ")

# Send the cURL input line by line.
for line in curl_input.splitlines():
    child.sendline(line)
time.sleep(0.5)  # Give time for input to be processed
# Detect OS and send appropriate EOF
if sys.platform.startswith('win'):
    child.sendcontrol('z')  # Ctrl+Z for Windows
else:
    child.sendcontrol('d')  # Ctrl+D for Linux/macOS

# Wait for the Save Video prompt and send the video_title name.
child.expect("Save Video as\\? ")
child.sendline(video_title)

# Hand over interactive control so you can see further output.
child.interact()
