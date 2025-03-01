#!/bin/bash
source install/python.sh
source install/hellyes.sh
source install/device_wvd.sh
source install/browsers.sh
source install/n_m3u8dl_re.sh
source install/ffmpeg.sh
source install/bento4.sh
# --- Main Installation ---

ensure_python_installed

install_hellyes

install_device_wvd

install_n_m3u8dl_re

install_ffmpeg

install_mp4decrypt

install_browsers_manifest

echo "✅ Installation complete!"
