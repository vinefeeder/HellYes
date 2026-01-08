# run script as superuser using command:-
# sudo bash Install-media-tools.sh

# Install MKVToolNix and ffmpeg from OS repos
# edit apt-get to the package manager on your system; dnf, pakman, yast, etc
apt-get update && \
    apt-get install -y mkvtoolnix mkvtoolnix-gui ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Bento4 (mp4decrypt)
wget https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip && \
    unzip -j Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip \
    'Bento4-SDK-1-6-0-641.x86_64-unknown-linux/bin/*' -d /usr/local/bin/ && \
    rm Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip && \
    chmod +x /usr/local/bin/*

# Install N_m3u8DL-RE
wget https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.3.0-beta/N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz && \
    tar -xzf N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz && \
    find . -name "N_m3u8DL-RE" -type f -exec mv {} /usr/local/bin/ \; && \
    chmod +x /usr/local/bin/N_m3u8DL-RE && \
    rm -rf N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz

# Install dash-mpd-cli
wget https://github.com/emarsden/dash-mpd-cli/releases/download/v0.2.29/dash-mpd-cli-linux-amd64
mv dash-mpd-cli-linux-amd64 /usr/local/bin/dash-mpd-cli && \
chmod +x /usr/local/bin/dash-mpd-cli

# Install uv by copying from official image
# cp --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
python -m pip install uv
