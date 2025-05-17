# Watermark Detector

A simple web application that detects if an image has a watermark using the Groq Vision API.

## Features

- Upload images via drag-and-drop or file selection
- Detect watermarks in images using AI
- Display detection results with explanations

## Requirements

- Python 3.6+
- Flask
- Requests
- Python-dotenv
- Groq API key

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd detect_water_marked
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```
pip install flask requests python-dotenv
```

4. Set up your Groq API key:
   - Create an account at https://console.groq.com/ if you don't have one
   - Get your API key from the Groq console
   - Create a `.env` file in the project root and add your API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

1. Start the application:
```
python app.py
```

2. Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

3. Upload an image and click "Detect Watermark" to analyze it.

## How It Works

1. The user uploads an image through the web interface
2. The image is sent to the Groq Vision API for analysis
3. The API determines if the image contains a watermark
4. The result is displayed to the user with an explanation

## License

MIT
