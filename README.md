# Video Screenshot Tool

A Python tool for extracting screenshots from video files at specific timestamps.

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage

```python
from src.screenshot_extractor import extract_screenshots_at_times

video_path = "path/to/video.mp4"
output_dir = "screenshots"
timestamps = [10, 30, 60]  # Screenshots at 10s, 30s, and 60s

extract_screenshots_at_times(video_path, output_dir, timestamps)
```