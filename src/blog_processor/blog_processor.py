import os
import logging
import traceback  # Added for detailed error reporting
from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from .docx_reader import BlogDocumentReader, MediaMarker
from .html_generator import HTMLGenerator
from .media_extractor import MediaExtractor


@dataclass
class ProcessingResult:
    """Stores the results of blog processing."""
    success: bool
    html_path: Optional[str] = None
    media_folder: Optional[str] = None
    errors: list[str] = None
    warnings: list[str] = None


class BlogProcessor:
    """Main coordinator for processing blog posts with media extraction."""

    def __init__(self, output_base_dir: str = "processed_blogs"):
        """Initialize the blog processor."""
        self.output_base_dir = output_base_dir
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the processor."""
        logger = logging.getLogger("BlogProcessor")
        logger.setLevel(logging.INFO)

        # Create handlers
        c_handler = logging.StreamHandler()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        f_handler = logging.FileHandler(f"blog_processing_{timestamp}.log")

        # Create formatters and add to handlers
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        c_format = logging.Formatter(format_str)
        f_format = logging.Formatter(format_str)
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

        return logger

    def _create_output_dirs(self, video_name: str) -> tuple[str, str]:
        """Create output directories for the blog post."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blog_dir = os.path.join(self.output_base_dir, f"{video_name}_{timestamp}")
        media_dir = os.path.join(blog_dir, video_name)

        os.makedirs(blog_dir, exist_ok=True)
        os.makedirs(media_dir, exist_ok=True)

        return blog_dir, media_dir

    def _extract_media(self, video_path: str, media_dir: str, markers: list[MediaMarker]) -> bool:
        """Extract all media files based on markers."""
        try:
            # Check if there are any markers to process
            if not markers:
                self.logger.warning("No media markers found to extract")
                print("WARNING: No media markers found to extract")
                return True  # Return True since there's nothing to extract

            # Log the markers for debugging
            self.logger.info(f"Extracting {len(markers)} media markers:")
            for i, marker in enumerate(markers):
                self.logger.info(f"  {i + 1}. {marker.type} at {marker.timestamp}s with align={marker.align}")
                print(f"Marker {i + 1}: {marker.type} at {marker.timestamp}s with align={marker.align}")

            # Create media extractor
            extractor = MediaExtractor(media_dir)

            # Extract all media
            success = extractor.extract_all_media(video_path, markers)

            if not success:
                self.logger.error("Media extraction failed")
                extractor.cleanup_failed_extractions()
                return False

            return True

        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Error extracting media: {str(e)}")
            self.logger.error(f"Error details: {error_details}")
            print(f"Error extracting media: {str(e)}")
            print(f"Error details: {error_details}")
            return False

    def process_blog(self, doc_path: str, video_path: str) -> ProcessingResult:
        """Process a blog post document with its associated video."""
        result = ProcessingResult(
            success=False,
            errors=[],
            warnings=[]
        )

        try:
            # Validate input files
            if not os.path.exists(doc_path):
                raise FileNotFoundError(f"Blog document not found: {doc_path}")
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # Create reader and parse document
            reader = BlogDocumentReader()
            print(f"Parsing document: {doc_path}")
            markers, blog_text = reader.extract_markers(doc_path)
            print(f"Found {len(markers)} media markers")

            # Validate markers
            warnings = reader.validate_markers(markers)
            if warnings:
                result.warnings.extend(warnings)
                self.logger.warning("Validation warnings:\n" + "\n".join(warnings))
                print("Validation warnings:")
                for warning in warnings:
                    print(f"  - {warning}")

            # Create output directories
            video_name = Path(video_path).stem
            blog_dir, media_dir = self._create_output_dirs(video_name)
            result.media_folder = media_dir
            print(f"Created output directories: {blog_dir}")

            # Check if we have any markers before proceeding
            if not markers:
                # No markers found, but we can still generate HTML without media
                print("No media markers found, generating HTML without media")
                # Generate HTML with no markers
                generator = HTMLGenerator(media_dir)
                html_content = generator.generate_html(blog_text, [])
                css_content = generator.generate_css()

                # Save HTML file
                html_path = os.path.join(blog_dir, "blog_post.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(f"{css_content}\n{html_content}")

                result.html_path = html_path
                result.success = True
                result.warnings.append("No media markers found in the document")
                return result

            # Extract media files
            print(f"Extracting media files from: {video_path}")
            if not self._extract_media(video_path, media_dir, markers):
                raise RuntimeError("Failed to extract media files")

            # Generate HTML
            generator = HTMLGenerator(media_dir)
            print("Generating HTML content")
            html_content = generator.generate_html(blog_text, markers)
            css_content = generator.generate_css()

            # Save HTML file
            html_path = os.path.join(blog_dir, "blog_post.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(f"{css_content}\n{html_content}")

            result.html_path = html_path
            result.success = True

            self.logger.info(f"Blog processing completed successfully!")
            self.logger.info(f"HTML saved to: {html_path}")
            self.logger.info(f"Media files saved to: {media_dir}")
            print("Blog processing completed successfully!")

        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = f"Error processing blog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Error details: {error_details}")
            print(f"Error processing blog: {str(e)}")
            print(f"Error details: {error_details}")
            result.errors.append(error_msg)

        return result