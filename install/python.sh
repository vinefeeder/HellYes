# Function to check if python3 and pip3 are available
check_python() {
    if command -v python3 &>/dev/null && command -v pip3 &>/dev/null; then
        return 0
    fi
    return 1
}

# Function to detect a popular package manager (reuse this from earlier)
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

# Function to ensure python3 and pip3 are installed
ensure_python_installed() {
    ESC_KEY=$'\e'
    while true; do
        if check_python; then
            echo -e "✅ python3 and pip3 are available!"
            break
        else
            echo -e "\n❌ python3 or pip3 not found."
            PKG_MANAGER=$(detect_package_manager)
            if [ -n "$PKG_MANAGER" ]; then
                echo "A package manager was detected: $PKG_MANAGER"
                echo -n "Do you want to run the install command for python3 and pip3 now? (y/n): "
                read -r ans
                if [[ "$ans" =~ ^[Yy]$ ]]; then
                    case "$PKG_MANAGER" in
                        apt-get)
                            echo "Running: sudo apt-get update && sudo apt-get install -y python3 python3-pip"
                            sudo apt-get update && sudo apt-get install -y python3 python3-pip
                            ;;
                        yum)
                            echo "Running: sudo yum install -y python3 python3-pip"
                            sudo yum install -y python3 python3-pip
                            ;;
                        dnf)
                            echo "Running: sudo dnf install -y python3 python3-pip"
                            sudo dnf install -y python3 python3-pip
                            ;;
                        pacman)
                            echo "Running: sudo pacman -S --noconfirm python python-pip"
                            sudo pacman -S --noconfirm python python-pip
                            ;;
                        brew)
                            echo "Running: brew install python3"
                            brew install python3
                            ;;
                        *)
                            echo "Unsupported package manager. Please install python3 and pip3 manually."
                            ;;
                    esac
                    sleep 2
                    continue  # Check again
                else
                    echo "Okay, please install python3 and pip3 manually."
                fi
            else
                echo "No supported package manager detected. Please install python3 and pip3 manually."
            fi

            echo "Press any key to try again, or press ESC to exit."
            read -rsn1 key
            if [[ "$key" == "$ESC_KEY" ]]; then
                echo -e "\nExiting as requested."
                exit 1
            fi
        fi
    done
}