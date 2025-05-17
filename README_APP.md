# Watermark Detector Desktop Application

A cross-platform desktop application for detecting watermarks in images using a trained PyTorch model.

## Features

- Simple and intuitive user interface
- Fast watermark detection using a pre-trained model
- Works offline without requiring internet connection
- Cross-platform (Windows and macOS)

## Installation

### Pre-built Binaries

1. Download the appropriate binary for your platform:
   - Windows: `WatermarkDetector.exe`
   - macOS: `WatermarkDetector.app`

2. Run the application:
   - Windows: Double-click the `.exe` file
   - macOS: Double-click the `.app` file (you may need to right-click and select "Open" the first time)

### Building from Source

#### Prerequisites

- Python 3.6 or higher
- PyQt5
- PyTorch and torchvision
- Pillow (PIL)
- PyInstaller (for creating executables)

#### Setup

1. Clone the repository or download the source code

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install PyQt5 torch torchvision pillow pyinstaller
   ```

4. Create the application icon:
   ```
   python create_icon.py
   ```

5. Run the application:
   ```
   python watermark_detector_app.py
   ```

6. Build the executable (optional):
   ```
   python build_app.py
   ```
   The executable will be created in the `dist` directory.

## Usage

1. Launch the application
2. Click the "Select Image" button to choose an image file
3. Click the "Detect Watermark" button to analyze the image
4. View the detection result and explanation

## How It Works

The application uses a ResNet18 model trained on a dataset of watermarked and non-watermarked images. The model analyzes the image and determines whether it contains a watermark based on visual patterns it has learned during training.

## Troubleshooting

### Common Issues

- **Application won't start**: Make sure you have all the required dependencies installed
- **Detection fails**: Ensure the image is in a supported format (JPG, PNG, BMP, WEBP)
- **Slow detection**: The first detection might be slower as the model loads into memory

### Error Messages

- **"Failed to load the selected image"**: The image file may be corrupted or in an unsupported format
- **"Detection failed"**: There was an error during the detection process, check the error message for details

## License

This project is licensed under the MIT License - see the LICENSE file for details.
