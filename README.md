# Blog Content Creator Tools

A comprehensive Python toolkit for creating blog content, including tools for extracting video clips and screenshots to enhance your blog posts, and processing blog content from various formats.

## Features

- **Blog Processing**: Convert and process blog content from various formats (like Word documents)
- **HTML Generation**: Generate clean HTML output for your blog posts
- **Media Extraction**: Extract and process media from your blog content
- **Video Clip Extraction**: Extract segments from videos to include in your blog posts
- **Screenshot Extraction**: Capture specific moments from videos as images

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
- Streamlit (for web interface)
- python-docx (for Word document handling)
- Other dependencies listed in `requirements.txt`

## Usage

### Processing Blog Content

```python
from blog_processor import blog_processor

# Process a blog post from a Word document
blog_processor.process_blog("path/to/document.docx", "output_directory")
```

### Converting Word Documents to HTML

```python
from blog_processor import docx_reader

# Convert a Word document to HTML
html_content = docx_reader.convert_docx_to_html("path/to/document.docx")
```

### Generating HTML Content

```python
from blog_processor import html_generator

# Generate HTML content with proper formatting
formatted_html = html_generator.generate_formatted_html(content, title)
```

### Extracting Media from Blog Content

```python
from blog_processor import media_extractor

# Extract and process media elements
media_extractor.process_media_elements(html_content, output_dir)
```

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

## Project Structure

```
blog-content-creator/
├── blog_processor/
│   ├── __init__.py
│   ├── blog_processor.py    # Main blog processing functionality
│   ├── docx_reader.py       # Word document parsing
│   ├── html_generator.py    # HTML content generation
│   └── media_extractor.py   # Extract media from blog content
├── src/
│   ├── __init__.py
│   ├── video_clipper.py     # Video clip extraction functionality
│   ├── screenshot_extractor.py # Screenshot extraction functionality
│   └── utils.py             # Shared utility functions
├── examples/
│   ├── example.py           # Example of screenshot extraction
│   └── clip_Example.py      # Example of video clip extraction
├── requirements.txt         # Project dependencies
└── README.md                # This documentation
```

## Web Interface

This project includes a Streamlit web interface for easy use:

```bash
streamlit run app.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.