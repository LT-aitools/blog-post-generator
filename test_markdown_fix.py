#!/usr/bin/env python3
"""
Test script to process a blog document with proper markdown formatting.
This script demonstrates how to apply the fix without modifying your existing code.

Usage:
    python test_blog_processor.py path/to/blog.docx path/to/video.mp4
"""

import os
import sys
import re
from pathlib import Path
import traceback
from datetime import datetime

# Add the project root to the Python path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if os.path.dirname(current_dir) else current_dir
sys.path.insert(0, project_root)

# Import the blog processor
try:
    from src.blog_processor import BlogProcessor
    from src.blog_processor.html_generator import HTMLGenerator
except ImportError:
    print("Error: Could not import the blog processor module.")
    print("Make sure you're running this script from the project directory.")
    print(f"Current directory: {os.getcwd()}")
    print(f"Project root set to: {project_root}")
    print("Available files in current directory:")
    for file in os.listdir(os.getcwd()):
        print(f"  {file}")
    sys.exit(1)


def patch_html_generator():
    """Patch the HTMLGenerator class to add markdown support."""

    # Add the markdown processing method
    def process_markdown_formatting(self, text):
        """Process markdown formatting to convert to HTML tags."""
        # Replace escaped headers with proper headers
        text = re.sub(r'\\#\s+(.+?)$', r'# \1', text, flags=re.MULTILINE)
        text = re.sub(r'\\##\s+(.+?)$', r'## \1', text, flags=re.MULTILINE)
        text = re.sub(r'\\###\s+(.+?)$', r'### \1', text, flags=re.MULTILINE)
        text = re.sub(r'\\####\s+(.+?)$', r'#### \1', text, flags=re.MULTILINE)

        # Fix list numbers that are escaped
        text = re.sub(r'\\(\d+)\.\s+(.+?)$', r'\1. \2', text, flags=re.MULTILINE)

        # Process italics (single asterisks)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Process bold (double asterisks)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        return text

    # Store the original generate_html method
    original_generate_html = HTMLGenerator.generate_html

    # Create a patched version that processes markdown first
    def new_generate_html(self, blog_text, markers):
        # Process markdown formatting first
        blog_text = self.process_markdown_formatting(blog_text)

        # Call the original method with the processed text
        return original_generate_html(self, blog_text, markers)

    # Add the new method to the class
    HTMLGenerator.process_markdown_formatting = process_markdown_formatting

    # Replace the generate_html method
    HTMLGenerator.generate_html = new_generate_html


def resolve_path(path):
    """Convert relative paths to absolute paths with home directory expansion."""
    # Expand user directory (~ or ~user)
    path = os.path.expanduser(path)

    # Check if path is already absolute
    if os.path.isabs(path):
        return path

    # Try the current directory
    if os.path.exists(path):
        return os.path.abspath(path)

    # Try in the Downloads folder
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    downloads_file = os.path.join(downloads_path, os.path.basename(path))
    if os.path.exists(downloads_file):
        return downloads_file

    # Try in the Desktop folder
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    desktop_file = os.path.join(desktop_path, os.path.basename(path))
    if os.path.exists(desktop_file):
        return desktop_file

    # Return the original path if none of the above worked
    return path


def main():
    """Main function to process a blog post with fixed markdown support."""
    if len(sys.argv) < 3:
        print("Usage: python test_blog_processor.py path/to/blog.docx path/to/video.mp4")
        sys.exit(1)

    # Get paths from command line arguments
    doc_path = resolve_path(sys.argv[1])
    video_path = resolve_path(sys.argv[2])

    print(f"Resolved document path: {doc_path}")
    print(f"Resolved video path: {video_path}")

    # Verify paths exist
    if not os.path.exists(doc_path):
        print(f"Error: Document not found at {doc_path}")
        print(f"Original path was: {sys.argv[1]}")
        print("Please provide the full path to the document.")
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        print(f"Original path was: {sys.argv[2]}")
        print("Please provide the full path to the video.")
        sys.exit(1)

    # Apply the patch to enable markdown formatting
    patch_html_generator()

    # Create the blog processor with an output directory based on timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"markdown_test_{timestamp}"
    processor = BlogProcessor(output_base_dir=output_dir)

    # Process the blog
    try:
        print(f"Processing blog document: {doc_path}")
        print(f"With video: {video_path}")
        print(f"Output will be in: {output_dir}")

        result = processor.process_blog(doc_path, video_path)

        if result.success:
            print("\n✅ Blog processing completed successfully!")
            print(f"HTML file: {result.html_path}")
            print(f"Media folder: {result.media_folder}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"- {warning}")

            # Open the HTML file in the default browser
            try:
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(result.html_path)}")
                print("\nOpened HTML file in your browser.")
            except:
                print(f"\nHTML file is at: {os.path.abspath(result.html_path)}")
        else:
            print("\n❌ Blog processing failed!")
            print("\nErrors:")
            for error in result.errors:
                print(f"- {error}")

    except Exception as e:
        print(f"Error processing blog: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main()