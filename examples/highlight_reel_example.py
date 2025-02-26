import os
import sys
from pathlib import Path

# Add the project root directory to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.highlight_reel_extractor import create_highlight_reel_from_file, extract_segments_from_text


def main():
    """Example of creating a highlight reel from a content specification file."""
    print("Highlight Reel Creator")
    print("---------------------")

    # Get the user's home directory
    home_dir = os.path.expanduser("~")

    # Default paths (you can modify these)
    default_video_path = os.path.join(home_dir, "Downloads", "interview.mp4")
    default_content_path = os.path.join(home_dir, "Documents", "highlight_content.txt")

    # Ask user for input paths
    print("\nPlease provide the following file paths (or press Enter for defaults):")

    user_video_path = input(f"Video file path [{default_video_path}]: ").strip()
    video_path = user_video_path if user_video_path else default_video_path

    user_content_path = input(f"Content file path [{default_content_path}]: ").strip()
    content_path = user_content_path if user_content_path else default_content_path

    # Allow user to paste content directly if they don't have a file
    if not os.path.exists(content_path):
        print("\nContent file not found. Would you like to paste content directly? (y/n)")
        use_direct_input = input().lower().startswith('y')

        if use_direct_input:
            print(
                "\nPaste your content specification below and press Ctrl+D (Unix) or Ctrl+Z (Windows) followed by Enter when done:")
            content_lines = []

            try:
                while True:
                    line = input()
                    content_lines.append(line)
            except EOFError:
                content = '\n'.join(content_lines)

                # Parse segments directly from the pasted content
                segments = extract_segments_from_text(content)

                if not segments:
                    print("No valid segments found in the pasted content.")
                    return

                print(f"\nFound {len(segments)} segments:")
                for i, segment in enumerate(segments, 1):
                    print(f"  {i}. {segment.title} (Start: {segment.start_time}s, Duration: {segment.duration}s)")

                # Create a temporary file with the content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    temp_file.write(content)
                    content_path = temp_file.name

        else:
            print("Content file is required. Please provide a valid file path.")
            return

    # Choose output directory
    default_output_dir = os.path.join(os.getcwd(), "highlight_reels")
    user_output_dir = input(f"Output directory [{default_output_dir}]: ").strip()
    output_dir = user_output_dir if user_output_dir else default_output_dir

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process the files
    try:
        print(f"\nCreating highlight reel from {video_path}")
        print(f"Using content from {content_path}")
        print(f"Output will be saved to {output_dir}\n")

        # Create the highlight reel
        output_path = create_highlight_reel_from_file(video_path, content_path, output_dir)

        print(f"\n✅ Highlight reel created successfully!")
        print(f"Output saved to: {output_path}")

    except Exception as e:
        print(f"\n❌ Error creating highlight reel: {str(e)}")


if __name__ == "__main__":
    main()