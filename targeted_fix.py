import os
import re
import sys
from pathlib import Path


def fix_image_paths(html_path):
    """Fix the image paths in the HTML file to point to the actual images."""
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return False

    # Read the HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Backup the original HTML
    backup_path = html_path + ".backup2"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Original HTML backed up to: {backup_path}")

    # Find all images in folder structure
    base_dir = os.path.dirname(html_path)
    real_images = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png')):
                real_images.append((file, os.path.join(root, file)))

    print(f"Found {len(real_images)} image files:")
    for name, path in real_images:
        print(f"  {name}: {path}")

    # Extract img src paths from HTML
    img_tags = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', html_content)
    print(f"\nFound {len(img_tags)} image references in HTML:")
    for tag in img_tags:
        print(f"  {tag}")

    # Create a mapping from HTML paths to real paths
    path_map = {}
    for img_src in img_tags:
        img_filename = os.path.basename(img_src)

        # Extract the timestamp part from filename
        timestamp_match = re.search(r'at_(\d+-\d+-\d+)\.jpg', img_filename)
        if not timestamp_match:
            print(f"  Could not extract timestamp from {img_filename}")
            continue

        timestamp = timestamp_match.group(1)
        print(f"  Looking for image with timestamp {timestamp}")

        # Find a matching real image
        for real_name, real_path in real_images:
            if timestamp in real_name:
                rel_path = os.path.relpath(real_path, base_dir)
                path_map[img_src] = rel_path
                print(f"  Mapped {img_src} → {rel_path}")
                break

    # Replace paths in HTML
    fixed_html = html_content
    for old_path, new_path in path_map.items():
        fixed_html = fixed_html.replace(f'src="{old_path}"', f'src="{new_path}"')

    # Write the fixed HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(fixed_html)

    print(f"\nFixed HTML saved to: {html_path}")
    return True


def main():
    print("Fixed Image Path Script")
    print("-" * 40)

    # Get input from user
    html_path = input("Enter the path to your blog HTML file: ").strip()

    if not html_path:
        print("Error: No path provided")
        return

    if not os.path.exists(html_path):
        print(f"Error: File not found: {html_path}")
        return

    if os.path.isdir(html_path):
        # If user provided a directory, look for blog_post.html
        html_path = os.path.join(html_path, "blog_post.html")
        if not os.path.exists(html_path):
            print(f"Error: blog_post.html not found in {html_path}")
            return

    print(f"Fixing image paths in: {html_path}")
    success = fix_image_paths(html_path)

    if success:
        # Try to open the file
        print("\nWould you like to open the HTML file in browser? (y/n):", end=" ")
        open_choice = input().strip().lower()
        if open_choice == 'y':
            try:
                import webbrowser
                webbrowser.open(f"file://{html_path}")
                print("Opened the HTML file in your browser")
            except:
                print("Please open the HTML file manually")


if __name__ == "__main__":
    main()