import os
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

    def generate_html(self, blog_text: str, markers: List[MediaMarker]) -> str:
        """Generate HTML from blog text and media markers."""
        # Create a copy of the blog text that we'll modify
        html_content = blog_text

        # Process each marker, replacing them with appropriate HTML
        for i, marker in enumerate(markers):
            if marker.type == 'CLIP':
                # For video clips
                time_str = str(timedelta(seconds=int(marker.timestamp))).replace(':', '-')
                duration_str = str(timedelta(seconds=int(marker.duration))).replace(':', '-')
                video_filename = f"{os.path.basename(self.media_folder)}_clip_from_{time_str}_duration_{duration_str}.mp4"
                video_path = os.path.join(self.media_folder_name, video_filename)
                html_element = self._create_video_element(marker, video_path)
            else:  # SCREENSHOT
                # For screenshots - match the naming pattern in media_extractor.py
                time_str = str(timedelta(seconds=int(marker.timestamp))).replace(':', '-')
                screenshot_filename = f"{os.path.basename(self.media_folder)}_screenshot_{i + 1:03d}_at_{time_str}.jpg"
                image_path = os.path.join(self.media_folder_name, screenshot_filename)
                html_element = self._create_image_element(marker, image_path)

            # Replace the marker with HTML
            html_content = html_content.replace(marker.original_text, html_element)

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