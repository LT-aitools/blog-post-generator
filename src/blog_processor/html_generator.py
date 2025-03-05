import os
import re
import glob
from typing import List
from datetime import timedelta
from .docx_reader import MediaMarker


class HTMLGenerator:
    """Generates HTML from blog text and media markers."""

    def __init__(self, media_folder: str):
        """Initialize the HTML generator."""
        self.media_folder = media_folder
        # Get just the folder name, not the full path
        self.media_folder_name = os.path.basename(media_folder)

        # Define patterns to match markers in text - updated to make align optional
        self.clip_pattern = r'\[CLIP\s+timestamp="([^"]+)"\s+duration="([^"]+)"(?:\s+align\s*[="]*([^"\]\s]+)["]?)?\]([^\[]*)'
        self.screenshot_pattern = r'\[SCREENSHOT\s+timestamp="([^"]+)"(?:\s+align\s*[="]*([^"\]\s]+)["]?)?\]([^\[]*)'

        # Immediately scan for all media files
        self.all_media_files = self._scan_for_media_files()
        self._log_media_files()

    def _log_media_files(self):
        """Log all found media files for debugging."""
        print(f"Found {len(self.all_media_files)} media files:")
        for i, (file_type, file_path) in enumerate(self.all_media_files):
            print(f"  {i + 1}. [{file_type}] {file_path}")

    def _scan_for_media_files(self):
        """Scan for all media files in the output directory and its subdirectories."""
        media_files = []

        # Walk through all subdirectories
        for root, dirs, files in os.walk(os.path.dirname(self.media_folder)):
            for file in files:
                if file.endswith('.jpg') or file.endswith('.jpeg'):
                    media_files.append(('SCREENSHOT', os.path.join(root, file)))
                elif file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.mov'):
                    media_files.append(('CLIP', os.path.join(root, file)))

        print(f"Scanned for media files in {self.media_folder}")
        return media_files

    def _create_video_element(self, marker: MediaMarker, video_path: str) -> str:
        """Create HTML for a video element with controlled width."""
        # Set width based on alignment
        width_class = self._get_width_class(marker.align)
        align_class = f"align-{marker.align}" if marker.align in ["left", "right"] else "align-center"

        return f"""
        <figure class="{align_class} {width_class}">
            <video controls>
                <source src="{video_path}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <figcaption>{marker.caption}</figcaption>
        </figure>
        """

    def _create_image_element(self, marker: MediaMarker, image_path: str) -> str:
        """Create HTML for an image element with controlled width."""
        # Set width based on alignment
        width_class = self._get_width_class(marker.align)
        align_class = f"align-{marker.align}" if marker.align in ["left", "right"] else "align-center"

        return f"""
        <figure class="{align_class} {width_class}">
            <img src="{image_path}" alt="{marker.caption}">
            <figcaption>{marker.caption}</figcaption>
        </figure>
        """

    def _get_width_class(self, align):
        """Get width class based on alignment."""
        if align == "left" or align == "right":
            return "width-50"
        elif align == "center":
            return "width-70"
        else:
            return "width-70"  # Default width

    def _find_media_file_by_timestamp(self, timestamp, media_type):
        """Find a media file by its timestamp."""
        # Convert timestamp to seconds for easier comparison
        if isinstance(timestamp, str):
            parts = timestamp.split(':')
            if len(parts) == 2:
                timestamp_secs = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                timestamp_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                timestamp_secs = int(timestamp)
        else:
            timestamp_secs = timestamp

        # Format timestamp for filename matching
        formatted_time = str(timedelta(seconds=timestamp_secs)).replace(':', '-')

        # Search for matching files
        for file_type, file_path in self.all_media_files:
            if file_type == media_type and formatted_time in file_path:
                # Return a path relative to the HTML output directory
                html_dir = os.path.dirname(self.media_folder)
                rel_path = os.path.relpath(file_path, html_dir)
                return rel_path

        # If no exact match, try a more flexible search
        for file_type, file_path in self.all_media_files:
            if file_type == media_type:
                # For screenshots, try matching by order/number
                if media_type == 'SCREENSHOT' and f"screenshot_{timestamp_secs:03d}" in file_path:
                    html_dir = os.path.dirname(self.media_folder)
                    rel_path = os.path.relpath(file_path, html_dir)
                    return rel_path

        print(f"WARNING: No {media_type} file found for timestamp {timestamp} ({formatted_time})")
        return None

    def _convert_markdown_headers(self, text):
        """Convert markdown headers to HTML."""
        # Replace ### headers
        text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        # Replace ## headers
        text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        # Replace # headers
        text = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        return text

    def _process_lists(self, text):
        """Process numbered lists and bullet points with dashes."""
        lines = text.split('\n')
        in_list = False
        in_numbered_list = False
        processed_lines = []

        # Track when we're inside figure content which should break list continuity
        in_figure = False
        section_counter = 0  # Use this to track different content sections

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detect figure content
            if '<figure' in stripped:
                in_figure = True

                # Close any open lists when we encounter a figure
                if in_numbered_list:
                    processed_lines.append('</ol>')
                    in_numbered_list = False
                elif in_list:
                    processed_lines.append('</ul>')
                    in_list = False

            if '</figure>' in stripped:
                in_figure = False
                # Increment section counter when we exit a figure
                section_counter += 1

            # Check if this is a header line with markdown syntax
            header_match = re.match(r'^#{1,6}\s+(.+)$', stripped)
            is_header = header_match is not None

            if is_header:
                # Close any open lists when encountering a header
                if in_numbered_list:
                    processed_lines.append('</ol>')
                    in_numbered_list = False
                elif in_list:
                    processed_lines.append('</ul>')
                    in_list = False

                # Increment section counter for each header
                section_counter += 1
                processed_lines.append(line)
                continue

            # Look for significant paragraph breaks that should start new numbered lists
            if i > 0 and stripped and re.match(r'^\d+\.', stripped):
                # If there's a blank line before this "NUMBER. " and we're in a list or
                # if this is after a figure, consider it a new section
                prev_line = lines[i - 1].strip() if i > 0 else ""

                # Check if we have a pattern indicating a new section
                new_section = False

                if prev_line == "":
                    # Blank line before numbered item
                    new_section = True
                elif not (prev_line.startswith("-") or re.match(r'^\d+\.', prev_line)):
                    # Previous line is not a list item
                    new_section = True
                elif in_figure or section_counter > 0:
                    # After a figure or a different content section
                    new_section = True

                if new_section and in_list:
                    # Close the current list before starting a new one
                    if in_numbered_list:
                        processed_lines.append('</ol>')
                        in_numbered_list = False
                    else:
                        processed_lines.append('</ul>')
                        in_list = False

                # Start a new section counter if needed
                if new_section:
                    section_counter += 1

            # Check for numbered list items (e.g., "1. Item")
            numbered_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
            # Check for bullet points with dashes
            dash_match = re.match(r'^-\s+(.+)$', stripped)

            if numbered_match:
                # Extract the actual number from the document
                list_number = numbered_match.group(1)
                list_content = numbered_match.group(2)

                # Decide if we need to start a new list or continue an existing one
                if not in_numbered_list:
                    # Start a new list with a style that keeps the original numbering
                    processed_lines.append(f'<ol class="preserve-numbers">')
                    in_numbered_list = True
                    in_list = True

                # Add the list item with value attribute to specify the number
                processed_lines.append(f'<li value="{list_number}">{list_content}</li>')
            elif dash_match:
                if in_numbered_list:
                    # Close the numbered list before starting an unordered list
                    processed_lines.append('</ol>')
                    in_numbered_list = False

                if not in_list or in_numbered_list:
                    # Start a new unordered list
                    processed_lines.append('<ul>')
                    in_list = True

                # Add the list item
                processed_lines.append(f'<li>{dash_match.group(1)}</li>')
            else:
                # For non-list items

                # Check if we have multiple consecutive blank lines (a stronger section break)
                if stripped == "" and i > 0 and i < len(lines) - 1:
                    next_line = lines[i + 1].strip()
                    prev_line = lines[i - 1].strip()

                    # Check if this is creating a significant break between sections
                    if prev_line == "" and re.match(r'^\d+\.', next_line):
                        # Strong section break with double blank line before new numbered list
                        if in_numbered_list:
                            processed_lines.append('</ol>')
                            in_numbered_list = False
                        elif in_list:
                            processed_lines.append('</ul>')
                            in_list = False

                        # Mark this as a new section
                        section_counter += 1

                # Close lists for any regular paragraph text (non-blank, non-list)
                if stripped and not stripped.startswith("-") and not re.match(r'^\d+\.', stripped):
                    if in_numbered_list:
                        processed_lines.append('</ol>')
                        in_numbered_list = False
                    elif in_list:
                        processed_lines.append('</ul>')
                        in_list = False

                # Add the line as is
                processed_lines.append(line)

        # Close any open lists at the end
        if in_numbered_list:
            processed_lines.append('</ol>')
        elif in_list:
            processed_lines.append('</ul>')

        return '\n'.join(processed_lines)

    def generate_html(self, blog_text: str, markers: List[MediaMarker]) -> str:
        """Generate HTML from blog text and media markers."""
        # Create a copy of the blog text that we'll modify
        html_content = blog_text

        # Debug - print the markers we received
        print(f"Processing {len(markers)} media markers:")
        for i, marker in enumerate(markers):
            print(f"  Marker {i + 1}: {marker.type} at {marker.timestamp}s - Original text: {marker.original_text}")

        # Process each marker, replacing them with appropriate HTML
        for i, marker in enumerate(markers):
            html_element = None

            if marker.type == 'CLIP':
                # Find matching video file
                video_path = self._find_media_file_by_timestamp(marker.timestamp, 'CLIP')
                if video_path:
                    html_element = self._create_video_element(marker, video_path)
                    print(f"  Created clip element with path: {video_path}")
            else:  # SCREENSHOT
                # Find matching screenshot file
                image_path = self._find_media_file_by_timestamp(marker.timestamp, 'SCREENSHOT')
                if image_path:
                    html_element = self._create_image_element(marker, image_path)
                    print(f"  Created screenshot element with path: {image_path}")

            # Replace marker with HTML if we found a matching media file
            if html_element and marker.original_text:
                if marker.original_text in html_content:
                    html_content = html_content.replace(marker.original_text, html_element)
                    print(f"  Replaced marker {i + 1} with HTML element for {marker.type}")
                else:
                    print(f"  WARNING: Marker text not found in content: {marker.original_text}")

                    # Try to find the marker using regex
                    if marker.type == 'SCREENSHOT':
                        pattern = r'\[SCREENSHOT\s+timestamp="([^"]+)"(?:\s+align\s*[="]*([^"\]\s]+)["]?)?\]'
                        matches = list(re.finditer(pattern, html_content))
                        if matches:
                            for match in matches:
                                # Check if timestamps are close
                                match_timestamp = match.group(1)
                                match_seconds = 0

                                try:
                                    parts = match_timestamp.split(':')
                                    if len(parts) == 2:
                                        match_seconds = int(parts[0]) * 60 + int(parts[1])
                                    elif len(parts) == 3:
                                        match_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                except:
                                    pass

                                if abs(match_seconds - marker.timestamp) < 5:  # Allow 5 second difference
                                    html_content = html_content.replace(match.group(0), html_element)
                                    print(f"  Replaced marker using regex: {match.group(0)}")
                                    break
            elif not html_element:
                print(f"  WARNING: No media file found for marker {i + 1}")

        # Check if we have any unprocessed markers
        remaining_markers = re.findall(r'\[SCREENSHOT[^\]]+\]', html_content)
        if remaining_markers:
            print(f"Found {len(remaining_markers)} unprocessed markers in output")
            for i, marker_text in enumerate(remaining_markers):
                print(f"  {i + 1}. {marker_text}")

            # Try to handle unprocessed markers by scanning for images
            screenshot_files = [path for file_type, path in self.all_media_files if file_type == 'SCREENSHOT']
            screenshot_files.sort()

            for i, marker_text in enumerate(remaining_markers):
                # Extract timestamp and align
                ts_match = re.search(r'timestamp="([^"]+)"', marker_text)
                align_match = re.search(r'align\s*[="]*([^"\]\s]+)["]?', marker_text)

                if ts_match and i < len(screenshot_files):
                    timestamp = ts_match.group(1)

                    # Default to "center" if align is None or empty
                    if align_match and align_match.group(1):
                        align = align_match.group(1).strip('"').strip()
                    else:
                        align = "center"

                    # Create HTML element with the next available screenshot
                    image_path = os.path.relpath(screenshot_files[i], os.path.dirname(self.media_folder))

                    # Create a temporary marker for the HTML generation
                    temp_marker = MediaMarker(
                        type='SCREENSHOT',
                        timestamp=0,
                        duration=None,
                        align=align,
                        caption=f"Screenshot at {timestamp}",
                        original_text=""
                    )

                    html_element = self._create_image_element(temp_marker, image_path)
                    html_content = html_content.replace(marker_text, html_element)
                    print(f"  Replaced unprocessed marker with image: {image_path}")

        # Process markdown headers and lists before splitting into paragraphs
        html_content = self._convert_markdown_headers(html_content)
        html_content = self._process_lists(html_content)

        # Split content by double newlines for paragraph processing
        paragraphs = html_content.split('\n\n')
        html_paragraphs = []

        for p in paragraphs:
            if p.strip():
                # Skip wrapping in <p> tags if the paragraph already contains HTML elements
                if re.search(r'<(h[1-6]|ul|ol|li|figure)', p):
                    html_paragraphs.append(p.strip())
                else:
                    # Check for single-line HTML elements
                    lines = p.strip().split('\n')
                    processed_lines = []

                    for line in lines:
                        # If the line already has HTML, don't wrap it in <p>
                        if re.search(r'<(h[1-6]|ul|ol|li|figure)', line):
                            processed_lines.append(line)
                        else:
                            # Wrap non-HTML lines in <p> tags
                            processed_lines.append(f'<p>{line}</p>')

                    html_paragraphs.append('\n'.join(processed_lines))

        # Create document structure that preserves formatting
        return '\n\n'.join(html_paragraphs)

    def generate_css(self) -> str:
        """Generate CSS for proper styling with width controls and markdown formatting."""
        return """
        <style>
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }

            p {
                margin: 0.7em 0;
            }

            /* Header styling to match markdown formatting */
            h1, h2, h3, h4, h5, h6 {
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                font-weight: bold;
            }

            h1 {
                font-size: 2em;
            }

            h2 {
                font-size: 1.5em;
            }

            h3 {
                font-size: 1.2em;
            }

            /* Lists styling */
            ul, ol {
                margin: 1em 0;
                padding-left: 2em;
            }

            li {
                margin-bottom: 0.5em;
            }

            /* Override default list counter styles */
            ol.preserve-numbers {
                counter-reset: none;
            }

            ol.preserve-numbers > li {
                list-style: none;
                position: relative;
            }

            ol.preserve-numbers > li::before {
                content: attr(value) ".";
                position: absolute;
                left: -2em;
                width: 1.5em;
                text-align: right;
            }

            /* Nested lists */
            li > ul, li > ol {
                margin-top: 0.5em;
            }

            figure {
                margin: 1.5em auto;
                text-align: center;
            }

            figure.align-left {
                float: left;
                margin-right: 20px;
                margin-bottom: 10px;
                text-align: left;
            }

            figure.align-right {
                float: right;
                margin-left: 20px;
                margin-bottom: 10px;
                text-align: right;
            }

            figure.align-center {
                clear: both;
                text-align: center;
            }

            /* Width classes */
            figure.width-50 {
                max-width: 50%;
            }

            figure.width-70 {
                max-width: 70%;
            }

            figure img, figure video {
                max-width: 100%;
                height: auto;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            figcaption {
                color: #666;
                font-size: 0.9em;
                margin-top: 0.5em;
                font-style: italic;
            }

            /* Clear floats after figures */
            .clearfix::after {
                content: "";
                clear: both;
                display: table;
            }
        </style>
        """