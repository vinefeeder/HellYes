# Function to check if mp4decrypt is available globally or in ./bin
check_mp4decrypt() {
    if command -v mp4decrypt &>/dev/null; then
        return 0
    fi
    if [ -x "./bin/mp4decrypt" ]; then
        return 0
    fi
    return 1
}

# Function to ensure mp4decrypt is installed or prompt the user to download it
install_mp4decrypt() {
    REPO_URL="https://www.bento4.com/downloads/"
    ESC_KEY=$'\e'

    while true; do
        if check_mp4decrypt; then
            echo -e "✅ mp4decrypt command found!"
            break
        else
            echo -e "\n❌ mp4decrypt command not found."
            echo "Please download mp4decrypt from:"
            echo "  ${REPO_URL}"
            echo "and place the executable in the ./bin directory."
            echo "Press any key to try again, or press ESC to exit."
            read -rsn1 key
            if [[ "$key" == "$ESC_KEY" ]]; then
                echo -e "\nExiting as requested."
                exit 1
            fi
        fi
    done
}
