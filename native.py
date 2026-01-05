#!/usr/bin/env venv/bin/python3
import sys
import struct
import json
import subprocess
import os
import datetime
import base64
import re

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

def main():
    try:
        # Read the incoming message from Chrome.
        message = read_message()
        manifest_url = message.get("manifestUrl", "")
        license_url = message.get("licenseUrl", "")
        header_string = message.get("headerString", "")
        headers = message.get("headers", "")
        license_data = message.get("licenseData", "")
        body_base_64 = message.get("bodyBase64", "")
        title = message.get("title", "")
        if not title:
            title = datetime.datetime.now().isoformat()  # Example: '2025-02-15T14:30:00.123456'

        # Sanitize title for use as filename (remove/replace invalid characters)
        title = re.sub(r'[<>:"/\\|?*]', '', title)  # Replace invalid chars with underscore
        title = title.strip()  # Remove leading/trailing whitespace

        data = {
            "manifestUrl": manifest_url,
            "licenseUrl": license_url,
            "headerString": header_string,
            "headers": headers,
            "licenseData": license_data,
            "bodyBase64": body_base_64,
            "title": title,
            "deleteMe": True

        }

        # Save the data in one JSON file with a name based on the current timestamp.
        folder_path = "pending"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # Ensure the folder exists

        file_path = os.path.join(folder_path, f"{title}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        # Save licenseData as binary (title.bin)
        if license_data:
            bin_path = os.path.join(folder_path, f"{title}.bin")
            with open(bin_path, "wb") as bf:
                bf.write(base64.b64decode(license_data))

        # Send a success response back to the extension.
        send_message({"status": "success", "message": f"Data written to {file_path}"})
    except Exception as e:
        # Send an error response back in case of an exception.
        send_message({"status": "error", "message": str(e)})

if __name__ == '__main__':
    main()
