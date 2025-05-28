#!/bin/bash

# Function to check if N_m3u8DL-RE is available
check_n_m3u8dl_re() {
    if command -v N_m3u8DL-RE &>/dev/null; then
        return 0
    fi
    if [ -x "./bin/N_m3u8DL-RE" ]; then
        return 0
    fi
    return 1
}

install_n_m3u8dl_re() {
  REPO_URL="https://github.com/nilaoda/N_m3u8DL-RE"
  ESC_KEY=$'\e'

  while true; do
      if check_n_m3u8dl_re; then
          echo -e "✅ N_m3u8DL-RE command found!"
          break
      else
          echo -e "\n❌ N_m3u8DL-RE command not found."
          echo "Please download it from:"
          echo "  ${REPO_URL}"
          echo "and place the executable in the ./bin directory."
          echo "Press any key to try again, or press ESC to exit."

          # Read one character (silent mode, no newline)
          read -rsn1 key
          if [[ "$key" == "$ESC_KEY" ]]; then
              echo -e "\nExiting as requested."
              exit 1
          fi
          # Otherwise, loop to check again
      fi
done
}