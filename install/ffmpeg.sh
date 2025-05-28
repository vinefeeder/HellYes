#!/bin/bash

# Function to check if ffmpeg is available globally or in ./bin
check_ffmpeg() {
    if command -v ffmpeg &>/dev/null; then
        return 0
    fi
    if [ -x "./bin/ffmpeg" ]; then
        return 0
    fi
    return 1
}

# Function to detect a popular package manager
detect_package_manager() {
    if command -v apt-get &>/dev/null; then
        echo "apt-get"
    elif command -v yum &>/dev/null; then
        echo "yum"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    elif command -v brew &>/dev/null; then
        echo "brew"
    else
        echo ""
    fi
}

# Function to install ffmpeg using a package manager if the user agrees
auto_install_ffmpeg() {
    local pkg_manager="$1"
    local install_cmd=""
    case "$pkg_manager" in
        apt-get)
            install_cmd="sudo apt-get update && sudo apt-get install -y ffmpeg"
            ;;
        yum)
            install_cmd="sudo yum install -y ffmpeg"
            ;;
        dnf)
            install_cmd="sudo dnf install -y ffmpeg"
            ;;
        pacman)
            install_cmd="sudo pacman -S --noconfirm ffmpeg"
            ;;
        brew)
            install_cmd="brew install ffmpeg"
            ;;
        *)
            return 1
            ;;
    esac

    echo "Running: $install_cmd"
    eval "$install_cmd"
}

# Function to check and install ffmpeg
install_ffmpeg() {
    REPO_URL="https://ffmpeg.org/download.html"
    ESC_KEY=$'\e'

    while true; do
        if check_ffmpeg; then
            echo -e "✅ ffmpeg command found!"
            break
        else
            echo -e "\n❌ ffmpeg command not found."
            PKG_MANAGER=$(detect_package_manager)
            if [ -n "$PKG_MANAGER" ]; then
                echo "A package manager was detected: $PKG_MANAGER"
                case "$PKG_MANAGER" in
                    apt-get)
                        echo "You can install ffmpeg automatically using: sudo apt-get install ffmpeg"
                        ;;
                    yum)
                        echo "You can install ffmpeg automatically using: sudo yum install ffmpeg"
                        ;;
                    dnf)
                        echo "You can install ffmpeg automatically using: sudo dnf install ffmpeg"
                        ;;
                    pacman)
                        echo "You can install ffmpeg automatically using: sudo pacman -S ffmpeg"
                        ;;
                    brew)
                        echo "You can install ffmpeg automatically using: brew install ffmpeg"
                        ;;
                esac
                echo -n "Do you want to run the install command now? (y/n): "
                read -r ans
                if [[ "$ans" =~ ^[Yy]$ ]]; then
                    if auto_install_ffmpeg "$PKG_MANAGER"; then
                        echo "Installation command executed. Checking for ffmpeg again..."
                        sleep 2
                        continue
                    else
                        echo "Error: Unable to run install command automatically."
                    fi
                else
                    echo "Okay, please install ffmpeg manually."
                fi
            else
                echo "No supported package manager detected."
            fi

            echo "Alternatively, download ffmpeg from:"
            echo "  ${REPO_URL}"
            echo "and place the executable in the ./bin directory."
            echo "Press any key to try again, or press ESC to exit."

            # Wait for one key press (without echo)
            read -rsn1 key
            if [[ "$key" == "$ESC_KEY" ]]; then
                echo -e "\nExiting as requested."
                exit 1
            fi
            # Loop will retry the check.
        fi
    done
}
