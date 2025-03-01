# Helper function to create device.wvd if client_id.bin and private_key.pem exist.
create_device() {
    if [ -f "client_id.bin" ] && [ -f "private_key.pem" ]; then
        echo "Found client_id.bin and private_key.pem. Creating device.wvd..."
        ./venv/bin/pywidevine create-device -k private_key.pem -c client_id.bin -t "ANDROID" -l 3

        # Expect a .wvd file in the current directory (pick the first one found)
        WVD_FILE=$(ls *.wvd 2>/dev/null | head -n1)
        if [ -n "$WVD_FILE" ]; then
            mv "$WVD_FILE" device.wvd
            echo -e "✅ device.wvd created successfully."
            return 0
        else
            echo "Error: The device file was not created."
            return 1
        fi
    else
        return 1
    fi
}

install_device_wvd() {
    ESC_KEY=$'\e'
    REPO_URL="https://forum.videohelp.com/threads/413719-Ready-to-use-CDMs-available-here"

    # If device.wvd already exists, we're done.
    if [ -f "device.wvd" ]; then
        echo -e "✅ device.wvd already exists."
        return 0
    fi

    # Try to create device.wvd if the required files exist.
    if create_device; then
        return 0
    fi

    # If creation failed because files are missing:
    echo -e "\n❌ Missing client_id.bin and/or private_key.pem."
    echo "Please either:"
    echo "  1) Place both client_id.bin and private_key.pem in the current directory, OR"
    echo "  2) Provide a link to a zip file containing them (they should be at the root of the zip)."
    echo -e "\033[1;33mYou can probably find these files here: ${REPO_URL}\033[0m"
    echo "Enter a zip file URL, or press Enter to try again after placing the files."
    echo "Press ESC at the prompt to exit."

    read -e -p "Enter zip file URL (or leave blank): " ZIP_URL
    # If the user types ESC and then Enter:
    if [ "$ZIP_URL" = "$ESC_KEY" ]; then
        echo -e "\nExiting as requested."
        exit 1
    fi

    if [ -n "$ZIP_URL" ]; then
        echo "Downloading zip file from: $ZIP_URL"
        TMP_ZIP=$(mktemp /tmp/cdm_zip.XXXXXX.zip)
        if curl -L "$ZIP_URL" -o "$TMP_ZIP"; then
            echo "Extracting zip file..."
            unzip -o "$TMP_ZIP" -d .
            rm -f "$TMP_ZIP"
            # Try to create device.wvd if the required files exist.
            if create_device; then
                return 0
            fi
        else
            echo "Error downloading zip file."
            rm -f "$TMP_ZIP"
        fi
    fi

    echo "Press any key to try again, or press ESC to exit."
    read -rsn1 key2
    if [[ "$key2" == "$ESC_KEY" ]]; then
        echo -e "\nExiting as requested."
        exit 1
    fi

    # Retry until device.wvd is created or the user exits.
    install_device_wvd
}
