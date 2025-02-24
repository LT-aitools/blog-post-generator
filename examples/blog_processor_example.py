import os
import sys
from pathlib import Path

# Add the project root directory to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.blog_processor import BlogProcessor


def main():
    print("Welcome to the Blog Media Processor!")
    print("-" * 40)

    # Get the desktop path for Mac
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

    # Set up specific paths for your files
    doc_path = os.path.join(desktop_path, "input_blogs", "4thblog.docx")
    video_path = os.path.join(desktop_path, "input_videos", "4threcording.mp4")

    # Print the exact paths being used
    print("\nAttempting to use these files:")
    print(f"Document path: {doc_path}")
    print(f"Video path: {video_path}")

    # Verify files exist
    if not os.path.exists(doc_path):
        print(f"\nError: Could not find document at {doc_path}")
        print("Please check that your blog document is in the correct location")
        input("\nPress Enter to exit...")
        return

    if not os.path.exists(video_path):
        print(f"\nError: Could not find video at {video_path}")
        print("Please check that your video is in the correct location")
        input("\nPress Enter to exit...")
        return

    print("\nFiles found successfully!")
    print("Processing your blog post...")

    # Initialize the blog processor
    processor = BlogProcessor(output_base_dir="processed_blogs")

    # Process the blog
    result = processor.process_blog(doc_path, video_path)

    if result.success:
        print("\n✅ Blog processing completed successfully!")
        print(f"\nOutputs:")
        print(f"  HTML file: {result.html_path}")
        print(f"  Media folder: {result.media_folder}")

        if result.warnings:
            print("\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        # Try to open output folder - Mac version
        try:
            os.system(f'open "{os.path.dirname(result.html_path)}"')
            print("\nOpened output folder for you!")
        except:
            print(f"\nOutput folder is at: {os.path.dirname(result.html_path)}")

    else:
        print("\n❌ Blog processing failed!")
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()