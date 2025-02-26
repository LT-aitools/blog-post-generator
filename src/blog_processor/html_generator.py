import os
import re
import glob
from typing import List
from datetime import timedelta
from .docx_reader import MediaMarker


class HTMLGenerator:
    """Generates Medium-compatible HTML from blog text and media markers."""

    def __init__(self, media_folder: str):
        """Initialize the HTML generator."""
        self.media_folder = media_folder
        # Get just the folder name, not the full path
        self.media_folder_name = os.path.basename(media_folder)

        # Define patterns to match markers in text
        self.clip_pattern = r'\[CLIP\s+timestamp="([^"]+)"\s+duration="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'
        self.screenshot_pattern = r'\[SCREENSHOT\s+timestamp="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'

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
        """Create HTML for a video element."""
        align_class = f"align-{marker.align}" if marker.align != "center" else ""
        return f"""
        <figure class="{align_class}">
            <video width="100%" controls>
                <source src="{video_path}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <figcaption>{marker.caption}</figcaption>
        </figure>
        """

    def _create_image_element(self, marker: MediaMarker, image_path: str) -> str:
        """Create HTML for an image element."""
        align_class = f"align-{marker.align}" if marker.align != "center" else ""
        return f"""
        <figure class="{align_class}">
            <img src="{image_path}" alt="{marker.caption}">
            <figcaption>{marker.caption}</figcaption>
        </figure>
        """

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
                        pattern = f'\\[SCREENSHOT\\s+timestamp="([^"]+)"\\s+align\\s*[="]*([^"\]\s]+)["]?\\]'
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

                if ts_match and align_match and i < len(screenshot_files):
                    timestamp = ts_match.group(1)
                    align = align_match.group(1)

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

        # Wrap paragraphs in <p> tags
        paragraphs = html_content.split('\n\n')
        html_paragraphs = [f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()]

        return '\n\n'.join(html_paragraphs)

    def generate_css(self) -> str:
        """Generate CSS for proper Medium styling."""
        return """
        <style>
            figure {
                margin: 2em 0;
                text-align: center;
            }

            figure.align-left {
                text-align: left;
            }

            figure.align-right {
                text-align: right;
            }

            figure img, figure video {
                max-width: 100%;
                height: auto;
            }

            figcaption {
                color: #666;
                font-size: 0.9em;
                margin-top: 0.5em;
            }
        </style>
        """