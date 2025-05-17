#!/bin/bash
echo "Starting Watermark Detector..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing required packages..."
    pip install PyQt5 torch torchvision pillow
fi
python watermark_detector_app.py
