#!/usr/bin/env venv/bin/python3
import sys
import struct
import json
import subprocess
import os
import datetime

def read_message():
    # Read the message length (first 4 bytes).
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        sys.exit(0)
    message_length = struct.unpack("I", raw_length)[0]
    # Read the JSON message.
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)

def send_message(message):
    # Convert message to JSON and encode it.
    encoded_message = json.dumps(message).encode("utf-8")
    # Write message length (first 4 bytes).
    sys.stdout.buffer.write(struct.pack("I", len(encoded_message)))
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()

def open_terminal_and_run_script():
    """
    Try to open a terminal emulator and execute the script 'erxpect.ppy'
    using Python in the current directory.
    """
    commands = [
        # Debian-based systems often have x-terminal-emulator.
        ["x-terminal-emulator", "-e", "./myenv/bin/python3", "./expect.py"],
        # GNOME terminal.
        ["gnome-terminal", "--", "python3", "./expect.py"],
        # KDE Konsole.
        ["konsole", "-e", "python3", "./expect.py"],
        # XFCE terminal.
        ["xfce4-terminal", "--command=python3 ./expect.py"],
        # xterm is widely available.
        ["xterm", "-e", "python3", "./expect.py"]
    ]
    for cmd in commands:
        try:
            subprocess.Popen(cmd)
            return  # Successfully launched a terminal.
        except FileNotFoundError:
            continue
    raise Exception("No supported terminal emulator found to execute erxpect.ppy.")


def main():
    try:
        # Read the incoming message from Chrome.
        message = read_message()
        manifest_url = message.get("manifestUrl", "")
        license_curl = message.get("licenseCurl", "")
        title = message.get("title", "")
        if not title:
            title = datetime.datetime.now().isoformat()  # Example: '2025-02-15T14:30:00.123456'

        # Write both parameters to /tmp/output.txt
        with open("manifestUrl.txt", "w") as f:
            f.write(manifest_url)
        with open("cUrl.txt", "w") as f:
            f.write(license_curl)
        with open("title.txt", "w") as f:
            f.write(title)
        # Open system popup with the manifest URL using Zenity
        if manifest_url:
            # Note: Ensure that Zenity is installed on your system.
            open_terminal_and_run_script()
        # Send a success response back to the extension.
        send_message({"status": "success", "message": "Data written to /tmp/output.txt"})
    except Exception as e:
        # Send an error response back in case of an exception.
        send_message({"status": "error", "message": str(e)})

if __name__ == '__main__':
    main()
