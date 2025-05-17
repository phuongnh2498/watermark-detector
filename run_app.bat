@echo off
echo Starting Watermark Detector...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing required packages...
    pip install PyQt5 torch torchvision pillow
)
python watermark_detector_app.py
pause
