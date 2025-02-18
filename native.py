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

def open_terminal_and_run_script(file_path):
    """
    Try to open a terminal emulator and execute the script 'allhell3.py'
    using Python in the current directory, then wait for a key press.
    """
    # Build the shell command that runs your script and waits for a key press.
    shell_cmd = f'./venv/bin/python3 ./allhell3.py "{file_path}"; echo; read -n1 -r -p "Press any key to continue..."'

    commands = [
        # Debian-based systems often have x-terminal-emulator.
        ["x-terminal-emulator", "-e", "bash", "-c", shell_cmd],
        # GNOME terminal.
        ["gnome-terminal", "--", "bash", "-c", shell_cmd],
        # KDE Konsole.
        ["konsole", "-e", "bash", "-c", shell_cmd],
        # XFCE terminal.
        ["xfce4-terminal", "--command", f"bash -c \"{shell_cmd}\""],
        # xterm is widely available.
        ["xterm", "-e", "bash", "-c", shell_cmd]
    ]

    for cmd in commands:
        try:
            subprocess.Popen(cmd)
            return  # Successfully launched a terminal.
        except FileNotFoundError:
            continue
    raise Exception("No supported terminal emulator found to execute allhell3.py.")


def main():
    try:
        # Read the incoming message from Chrome.
        message = read_message()
        manifest_url = message.get("manifestUrl", "")
        license_curl = message.get("licenseCurl", "")
        title = message.get("title", "")
        if not title:
            title = datetime.datetime.now().isoformat()  # Example: '2025-02-15T14:30:00.123456'

        data = {
            "manifestUrl": manifest_url,
            "licenseCurl": license_curl,
            "title": title,
            "deleteMe": True
        }

        # Save the data in one JSON file with a name based on the current timestamp.
        file_path = f"{title}.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        # Open system popup with the manifest URL using Zenity (if applicable)
        if manifest_url:
            # Ensure that Zenity is installed on your system.
            open_terminal_and_run_script(file_path)

        # Send a success response back to the extension.
        send_message({"status": "success", "message": f"Data written to {file_path}"})
    except Exception as e:
        # Send an error response back in case of an exception.
        send_message({"status": "error", "message": str(e)})

if __name__ == '__main__':
    main()
