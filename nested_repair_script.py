import os
import sys
import glob
from pathlib import Path


def add_screenshots_to_html(blog_dir):
    """Add screenshots to the blog post HTML file."""
    # Find the HTML file
    html_path = os.path.join(blog_dir, "blog_post.html")
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return False

    # Print all files and folders recursively to debug
    print("Searching for images recursively...")
    all_images = []

    for root, dirs, files in os.walk(blog_dir):
        for file in files:
            if file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.png'):
                full_path = os.path.join(root, file)
                all_images.append(full_path)
                print(f"Found image: {full_path}")

    if not all_images:
        print(f"Error: No image files found in {blog_dir} or its subfolders")
        return False

    all_images.sort()
    print(f"Found a total of {len(all_images)} image files")

    # Read the HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Check if the HTML already has image tags
    if "<img" in html_content:
        print("HTML already contains image tags. No changes needed.")
        return False

    # Find the end of the style section
    style_end = html_content.find("</style>")
    if style_end < 0:
        # No style tag found, look for the first paragraph
        insert_pos = html_content.find("<p>")
        if insert_pos < 0:
            print("Error: Could not find a suitable position to insert images")
            return False
    else:
        # Insert after the style tag
        insert_pos = style_end + 8  # Length of "</style>"

    # Create HTML for all screenshots
    screenshots_html = "<h2>Screenshots</h2>\n"
    for i, screenshot_file in enumerate(all_images):
        # Create a path relative to the HTML file
        rel_path = os.path.relpath(screenshot_file, os.path.dirname(html_path))
        screenshots_html += f"""
        <figure>
            <img src="{rel_path}" alt="Screenshot {i + 1}">
            <figcaption>Screenshot {i + 1} - {os.path.basename(screenshot_file)}</figcaption>
        </figure>
        """

    # Insert the screenshots into the HTML
    new_html = html_content[:insert_pos] + screenshots_html + html_content[insert_pos:]

    # Save the updated HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"Added {len(all_images)} screenshots to {html_path}")
    return True


def main():
    print("Nested Folder Repair Script")
    print("-" * 40)

    # Get input from user
    blog_dir = input("Enter the path to your blog output folder: ").strip()

    if not blog_dir:
        print("Error: No path provided")
        return

    if not os.path.isdir(blog_dir):
        print(f"Error: Directory not found: {blog_dir}")
        return

    result = add_screenshots_to_html(blog_dir)

    if result:
        print("\nHTML has been updated. Please open it to check if screenshots appear now.")
        html_path = os.path.join(blog_dir, "blog_post.html")
        print(f"HTML file: {html_path}")

        # Try to open the file
        try:
            import webbrowser
            webbrowser.open(f"file://{html_path}")
            print("Opened the HTML file in your browser")
        except:
            print("Please open the HTML file manually")


if __name__ == "__main__":
    main()