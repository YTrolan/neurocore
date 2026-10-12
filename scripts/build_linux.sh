#!/usr/bin/env bash
set -e

echo '=== NeuroCore Linux build ==='

if command -v apt-get &> /dev/null; then
    sudo apt-get install -y \
        libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0 \
        libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
        libxcb-render-util0 libxcb-shape0 libdbus-1-3 \
        libegl1 libgl1 libglib2.0-0 libfontconfig1
fi

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --name NeuroCore --onefile --noconfirm --clean --log-level ERROR \
    --hidden-import wasmtime --hidden-import numpy \
    --collect-all opendeep --collect-all curl_cffi \
    --collect-all wasmtime --collect-all numpy \
    --collect-all pyte --collect-all pyperclip \
    run.py

mv dist/NeuroCore dist/NeuroCore-linux-x64
echo '=== Готово: dist/NeuroCore-linux-x64 ==='
