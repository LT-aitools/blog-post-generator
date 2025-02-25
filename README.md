# Blog Content Creator Tools

A comprehensive Python toolkit for creating blog content, including tools for extracting video clips and screenshots to enhance your blog posts.

## Features

- **Video Clip Extraction**: Extract segments from videos to include in your blog posts
- **Screenshot Extraction**: Capture specific moments from videos as images
- **Blog Post Support**: Tools designed to help streamline the creation of multimedia blog content

## Installation

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Requirements

- Python 3.7+
- FFmpeg (for video processing)
- OpenCV
- Other dependencies listed in `requirements.txt`

## Usage

### Extracting Screenshots from Videos

```python
from src.screenshot_extractor import extract_screenshots_at_times

video_path = "path/to/video.mp4"
output_dir = "screenshots"
timestamps = [10, 30, 60]  # Screenshots at 10s, 30s, and 60s

extract_screenshots_at_times(video_path, output_dir, timestamps)
```

### Extracting Video Clips

```python
from src.video_clipper import extract_video_clip

video_path = "path/to/video.mp4"
output_dir = "clips"
start_time = 90  # Start at 1 minute 30 seconds
duration = 30    # 30 second clip

extract_video_clip(video_path, output_dir, start_time, duration)
```

### Helper Functions

The examples directory contains helper scripts that demonstrate how to use the core functionality:

- `example.py`: Shows how to extract screenshots from a video file
- `clip_Example.py`: Demonstrates extracting video clips

## Project Structure

```
blog-content-creator/
├── src/
│   ├── __init__.py
│   ├── video_clipper.py      # Video clip extraction functionality
│   ├── screenshot_extractor.py # Screenshot extraction functionality
│   └── utils.py              # Shared utility functions
├── examples/
│   ├── example.py            # Example of screenshot extraction
│   └── clip_Example.py       # Example of video clip extraction
├── requirements.txt          # Project dependencies
└── README.md                 # This documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.