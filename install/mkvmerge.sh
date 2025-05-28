#!/bin/bash
#
# Functions to verify and (manually) install mkvmerge
# Requires the user to fetch MKVToolNix from https://mkvtoolnix.download/downloads.html
#

# ── internal utility ────────────────────────────────────────────────────────────
check_mkvmerge() {
    # 1. global path?  2. ./bin/mkvmerge?
    if command -v mkvmerge &>/dev/null; then
        return 0
    fi
    if [ -x "./bin/mkvmerge" ]; then
        return 0
    fi
    return 1
}

# ── public API ─────────────────────────────────────────────────────────────────
install_mkvmerge() {
    local REPO_URL="https://mkvtoolnix.download/downloads.html"
    local ESC_KEY=$'\e'

    while true; do
        if check_mkvmerge; then
            echo -e "✅ mkvmerge command found!"
            break
        else
            echo -e "\n❌ mkvmerge command not found."
            echo "Please download MKVToolNix from:"
            echo "  ${REPO_URL}"
            echo "and place the executable 'mkvmerge'"
            echo "into the ./bin directory of this project."
            echo
            echo "Press any key to re-check, or press ESC to abort."
            read -rsn1 key
            if [[ "$key" == "$ESC_KEY" ]]; then
                echo -e "\nExiting as requested."
                exit 1
            fi
        fi
    done
}
