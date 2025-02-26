import os
import sys
import re
from pathlib import Path

# Add the project root directory to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


# Test HTML generation directly
def fix_html_manually(html_path):
    """Directly modify the HTML file to replace any remaining screenshot markers."""

    print(f"Fixing HTML file: {html_path}")

    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return False

    # Read the HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Check if there are any screenshot markers
    screenshot_pattern = r'\[SCREENSHOT\s+timestamp="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'

    # Find all screenshot markers
    matches = list(re.finditer(screenshot_pattern, html_content))
    print(f"Found {len(matches)} unreplaced screenshot markers")

    if not matches:
        print("No screenshot markers found in the HTML. The issue might be elsewhere.")
        return False

    # For each match, create replacement HTML
    for i, match in enumerate(matches):
        timestamp_str, align, caption = match.groups()
        print(f"  Marker {i + 1}: timestamp={timestamp_str}, align={align}, caption={caption}")

        # Convert timestamp to seconds for filename
        timestamp_seconds = 0
        parts = timestamp_str.split(':')
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            timestamp_seconds = minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            timestamp_seconds = hours * 3600 + minutes * 60 + seconds

        # Get the media folder path (one level down from the HTML file)
        html_dir = os.path.dirname(html_path)
        folder_name = os.path.basename(html_dir)

        # Find all files in the folder
        media_folder = os.path.join(html_dir, folder_name)
        if os.path.exists(media_folder):
            screenshot_files = [f for f in os.listdir(media_folder) if f.endswith('.jpg')]
            print(f"  Found {len(screenshot_files)} screenshot files in {media_folder}")

            # Look for screenshots with matching timestamps
            matching_files = []
            for filename in screenshot_files:
                if f"at_0-{timestamp_seconds:02d}-00" in filename:
                    matching_files.append(filename)

            if matching_files:
                print(f"  Found matching files: {matching_files}")
                image_path = os.path.join(folder_name, matching_files[0])

                # Create HTML element
                align_class = f"align-{align}" if align != "center" else ""
                html_element = f"""
                <figure class="{align_class}">
                    <img src="{image_path}" alt="{caption}">
                    <figcaption>{caption}</figcaption>
                </figure>
                """

                # Replace the marker
                html_content = html_content.replace(match.group(0), html_element)
                print(f"  Replaced marker with HTML for {image_path}")
            else:
                print(f"  No matching files found for timestamp {timestamp_str}")
        else:
            print(f"  Media folder not found: {media_folder}")

    # Write the updated HTML back to the file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML file updated with {len(matches)} marker replacements")
    return True


def main():
    print("Screenshot Marker Debug Script")
    print("-" * 50)

    # Get input from user
    html_path = input("Enter the full path to your blog HTML file: ").strip()

    if not html_path:
        print("Error: No path provided")
        return

    result = fix_html_manually(html_path)

    if result:
        print("\nHTML has been updated. Please open it to check if screenshots appear now.")
        print(f"HTML file: {html_path}")
    else:
        print("\nNo changes were made to the HTML file.")


if __name__ == "__main__":
    main()