# Blog Media Processor

A Python tool for processing blog posts with media markers to automatically extract video clips and screenshots from a source video.

## Features

- Supports both Word documents (.docx) and text files (.txt)
- Extracts video clips with specified duration
- Captures screenshots at specific timestamps
- Configurable media alignment and captions
- Detailed logging and error reporting

## How it works
- See "Directory_ExplanationOfFiles" for full explanation of the different files and how they fit together, for the blog processor to work.

## Charlie notes on usage 

Prior to this: 
1. Run the Whisper project to get the transscript with timestamps. 
2. Add the Granola notes and the transcript to the Claude project, and ask it to run the analysis prompt first, then the blog one. Edit if needed. 
3. Copy with no formatting (cmd shift v) to GDocs, and save as .docx
4. Create a Medium placeholder blog post, to grab the URL. 
5. Ask Claude to run the social media prompt, and then save the outputs to Drive.

To run the blog post processor:

1. [first-time setup only] Create and activate a virtual environment, install the dependencies, and install the package in development mode:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS
pip install -r requirements.txt
pip install -e .
```

2 Run the processor:
```bash
python run_processor.py
```

3. A UI window will pop up where you can:
   - Select your blog text file (with media markers)
   - Select your meeting video file
   - Click "Process Blog" to start

4. The processor will:
   - Extract screenshots and video clips based on the markers
   - Generate an HTML file with all content and media
   - Save everything to the `processed_blogs` folder

5. After processing:
   - Check the outputs in the `processed_blogs` folder
   - Once you've verified everything, you can move the outputs to Drive
   - Delete the contents of `processed_blogs` to keep the folder clean for next time

## Media Markers

The processor recognizes two types of media markers in your blog document:

1. **Video Clips**:
```
[CLIP timestamp="1:30" duration="5" align="center"]Optional caption text[/CLIP]
```

2. **Screenshots**:
```
[SCREENSHOT timestamp="2:45" align="center"]Optional caption text[/SCREENSHOT]
```

Timestamps can be specified in the following formats:
- `MM:SS` (e.g., "1:30")
- `HH:MM:SS` (e.g., "00:01:30")
- Seconds (e.g., "90" or "90.5")

## Error Handling

The processor includes comprehensive error handling and logging:
- Invalid timestamps or durations
- Missing or inaccessible files
- Media extraction failures
- Duplicate timestamps

All errors and warnings are logged to the console with appropriate context.

## Requirements

- Python 3.7 or higher
- PyQt6 (for the UI)
- python-docx (for Word document processing)
- moviepy (for video processing)
- imageio (for image handling)
- OpenCV (for video processing)

## License

This project is licensed under the MIT License - see the LICENSE file for details.


