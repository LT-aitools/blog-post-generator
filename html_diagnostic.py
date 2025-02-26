import os
import re
import sys
from pathlib import Path


def analyze_html(html_path):
    """Analyze the HTML file to find any image tags and markers."""
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return False

    # Read the HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Search for img tags
    img_tags = re.findall(r'<img[^>]+>', html_content)
    print(f"Found {len(img_tags)} <img> tags in HTML:")
    for i, tag in enumerate(img_tags[:10]):  # Show first 10 to avoid clutter
        print(f"  {i + 1}. {tag}")

    if len(img_tags) > 10:
        print(f"  ... and {len(img_tags) - 10} more")

    # Search for screenshot markers
    screenshot_markers = re.findall(r'\[SCREENSHOT[^\]]+\]', html_content)
    print(f"\nFound {len(screenshot_markers)} [SCREENSHOT] markers in HTML:")
    for i, marker in enumerate(screenshot_markers[:10]):
        print(f"  {i + 1}. {marker}")

    if len(screenshot_markers) > 10:
        print(f"  ... and {len(screenshot_markers) - 10} more")

    # Check for figure tags
    figure_tags = re.findall(r'<figure[^>]*>.*?</figure>', html_content, re.DOTALL)
    print(f"\nFound {len(figure_tags)} <figure> elements in HTML:")
    for i, tag in enumerate(figure_tags[:5]):  # Show first 5 to avoid clutter
        # Truncate long figure tags
        tag_preview = tag[:100] + "..." if len(tag) > 100 else tag
        print(f"  {i + 1}. {tag_preview}")

    if len(figure_tags) > 5:
        print(f"  ... and {len(figure_tags) - 5} more")

    # Check for broken image paths
    broken_paths = []
    for tag in img_tags:
        src_match = re.search(r'src="([^"]+)"', tag)
        if src_match:
            img_path = src_match.group(1)
            full_path = os.path.join(os.path.dirname(html_path), img_path)
            if not os.path.exists(full_path):
                broken_paths.append((img_path, full_path))

    if broken_paths:
        print("\nFound broken image paths:")
        for i, (img_path, full_path) in enumerate(broken_paths):
            print(f"  {i + 1}. HTML path: {img_path}")
            print(f"     Full path: {full_path}")
    else:
        print("\nNo broken image paths found.")

    # Create a fixed version
    if broken_paths:
        print("\nWould you like to fix the broken image paths? (y/n):", end=" ")
        fix_choice = input().strip().lower()
        if fix_choice == 'y':
            # Backup the original HTML
            backup_path = html_path + ".backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Original HTML backed up to: {backup_path}")

            # Find all images in folder structure
            base_dir = os.path.dirname(html_path)
            all_images = []
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        all_images.append(os.path.join(root, file))

            # Replace broken paths
            fixed_html = html_content
            for img_path, full_path in broken_paths:
                # Try to find a matching file
                for image_file in all_images:
                    if os.path.basename(image_file) == os.path.basename(img_path):
                        new_path = os.path.relpath(image_file, base_dir)
                        fixed_html = fixed_html.replace(f'src="{img_path}"', f'src="{new_path}"')
                        print(f"Replaced: {img_path} → {new_path}")
                        break

            # Save the fixed HTML
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(fixed_html)
            print(f"Fixed HTML saved to: {html_path}")

    return True


def main():
    print("HTML Diagnostic Script")
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

    print(f"Analyzing HTML file: {html_path}")
    analyze_html(html_path)

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