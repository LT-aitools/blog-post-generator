# Directory Structure and File Explanations

## Root Directory Files
- `run_processor.py` - Main entry point that launches the PyQt6 UI for the blog processor
- `requirements.txt` - Lists all Python package dependencies needed to run the project
- `README.md` - Project documentation and usage instructions
- `setup.py` - Python package configuration file
- `packages.txt` - Additional package dependencies (if any)
- `.gitignore` - Specifies which files Git should ignore
- `.DS_Store` - macOS system file (can be ignored)

## Core Source Code (`src/`)
### Blog Processor Module (`src/blog_processor/`)
- `blog_processor.py` - Main coordinator class that orchestrates the entire blog processing workflow
- `html_generator.py` - Generates the HTML output with proper formatting, styling, and media integration
- `docx_reader.py` - Reads and parses the blog text file, including media markers and content structure
- `media_extractor.py` - Handles extracting screenshots and video clips from the source video
- `__init__.py` - Makes the blog_processor directory a proper Python package

### Utility Modules (`src/`)
- `screenshot_extractor.py` - Core functionality for taking screenshots from videos at specific timestamps
- `videoclipper.py` - Core functionality for extracting video clips with specified durations
- `utils.py` - Common utility functions used across the project
- `__init__.py` - Makes the src directory a proper Python package

## UI Code (`examples/`)
- `corrected_blog_processor_ui.py` - PyQt6-based user interface for file selection and processing
- `.DS_Store` - macOS system file (can be ignored)

## Output Directory
- `processed_blogs/` - Directory where all processed outputs are saved, including:
  - HTML files
  - Extracted screenshots
  - Video clips
  - Media files

## Development Files
- `.venv/` - Python virtual environment containing project dependencies
- `.git/` - Git version control repository
- `.idea/` - PyCharm IDE settings (if using PyCharm)
- `tests/` - Test files for development and verification

## File Dependencies
The blog processor works by:
1. `run_processor.py` launches the UI
2. User selects input files through the UI
3. `blog_processor.py` coordinates the process:
   - `docx_reader.py` reads the blog text
   - `media_extractor.py` extracts media using `screenshot_extractor.py` and `videoclipper.py`
   - `html_generator.py` creates the final HTML output
4. All outputs are saved to `processed_blogs/` 