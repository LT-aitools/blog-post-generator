import os
import sys
import logging
import traceback
from typing import List, Dict
from pathlib import Path
from datetime import datetime, timedelta

# Adjust imports for Streamlit Cloud compatibility
try:
    # Try relative import first (how it works locally)
    from ..videoclipper import extract_video_clip
    from ..screenshot_extractor import extract_screenshots_at_times
except ImportError:
    # Alternative import for Streamlit Cloud
    from src.videoclipper import extract_video_clip
    from src.screenshot_extractor import extract_screenshots_at_times

from .docx_reader import MediaMarker


class MediaExtractor:
    """Handles extraction and organization of media files from video."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.logger = logging.getLogger("MediaExtractor")

        # Ensure logger is configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Track extracted files
        self.extracted_files: Dict[str, List[str]] = {
            'clips': [],
            'screenshots': []
        }

    def extract_all_media(self, video_path: str, markers: List[MediaMarker]) -> bool:
        """Extract all media files based on the markers."""
        try:
            # Add more detailed logging
            self.logger.info(f"Starting media extraction from: {video_path}")
            self.logger.info(f"Output directory: {self.output_dir}")
            self.logger.info(f"Total markers: {len(markers)}")
            print(f"Starting media extraction from: {video_path}")
            print(f"Output directory: {self.output_dir}")
            print(f"Total markers: {len(markers)}")

            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # Try to get video file details for debugging
            try:
                file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
                self.logger.info(f"Video file size: {file_size:.2f} MB")
                print(f"Video file size: {file_size:.2f} MB")
            except Exception as e:
                self.logger.warning(f"Could not get video file details: {str(e)}")
                print(f"Could not get video file details: {str(e)}")

            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.info(f"Created output directory: {self.output_dir}")

            # Check if we have any markers to process
            if not markers:
                self.logger.warning("No markers to extract")
                print("Warning: No markers to extract")
                return True

            # Categorize markers
            screenshot_markers = [m for m in markers if m.type == 'SCREENSHOT']
            clip_markers = [m for m in markers if m.type == 'CLIP']

            self.logger.info(f"Found {len(screenshot_markers)} screenshot markers and {len(clip_markers)} clip markers")
            print(f"Found {len(screenshot_markers)} screenshot markers and {len(clip_markers)} clip markers")

            # Extract screenshots first (more efficient to do in batch)
            if screenshot_markers:
                try:
                    self._extract_screenshots(video_path, screenshot_markers)
                except Exception as e:
                    error_details = traceback.format_exc()
                    self.logger.error(f"Error extracting screenshots: {str(e)}")
                    self.logger.error(f"Error details: {error_details}")
                    print(f"Error extracting screenshots: {str(e)}")
                    print(f"Error details: {error_details}")
                    return False

            # Extract video clips
            if clip_markers:
                try:
                    self._extract_clips(video_path, clip_markers)
                except Exception as e:
                    error_details = traceback.format_exc()
                    self.logger.error(f"Error extracting clips: {str(e)}")
                    self.logger.error(f"Error details: {error_details}")
                    print(f"Error extracting clips: {str(e)}")
                    print(f"Error details: {error_details}")
                    return False

            self.logger.info("Media extraction completed successfully")
            print("Media extraction completed successfully")
            return True

        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Error during media extraction: {str(e)}")
            self.logger.error(f"Error details: {error_details}")
            print(f"Error during media extraction: {str(e)}")
            print(f"Error details: {error_details}")
            return False

    def _extract_screenshots(self, video_path: str, markers: List[MediaMarker]) -> None:
        """Extract all screenshots in batch."""
        try:
            self.logger.info(f"Extracting {len(markers)} screenshots...")
            print(f"Extracting {len(markers)} screenshots...")

            # Get all timestamps and log them for debugging
            timestamps = []
            for i, marker in enumerate(markers):
                if isinstance(marker.timestamp, (int, float)):
                    timestamps.append(marker.timestamp)
                    self.logger.info(f"  Screenshot {i + 1}: timestamp={marker.timestamp}s")
                    print(f"  Screenshot {i + 1}: timestamp={marker.timestamp}s")
                else:
                    self.logger.error(
                        f"  Invalid timestamp for screenshot {i + 1}: {marker.timestamp} (type: {type(marker.timestamp)})")
                    print(
                        f"  Invalid timestamp for screenshot {i + 1}: {marker.timestamp} (type: {type(marker.timestamp)})")

            if not timestamps:
                self.logger.warning("No valid timestamps for screenshots")
                print("Warning: No valid timestamps for screenshots")
                return

            # Log the timestamps for debugging
            self.logger.info(f"Screenshot timestamps: {timestamps}")
            print(f"Screenshot timestamps: {timestamps}")

            # Extract screenshots
            extract_screenshots_at_times(video_path, self.output_dir, timestamps)
            self.logger.info(f"Screenshots extracted successfully to {self.output_dir}")
            print(f"Screenshots extracted successfully to {self.output_dir}")

            # Track extracted files
            for i, marker in enumerate(markers):
                if isinstance(marker.timestamp, (int, float)):
                    time_str = str(timedelta(seconds=int(marker.timestamp))).replace(':', '-')
                    basename = os.path.basename(video_path)
                    video_name = os.path.splitext(basename)[0]

                    # Match the filename format used in screenshot_extractor.py
                    filename = f"{video_name}_screenshot_{i + 1:03d}_at_{time_str}.jpg"
                    filepath = os.path.join(self.output_dir, filename)
                    self.extracted_files['screenshots'].append(filepath)

                    # Check if the file was actually created
                    if os.path.exists(filepath):
                        self.logger.info(f"  Created screenshot: {filename}")
                        print(f"  Created screenshot: {filename}")
                    else:
                        self.logger.warning(f"  Expected screenshot not found: {filename}")
                        print(f"  Warning: Expected screenshot not found: {filename}")

        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Error extracting screenshots: {str(e)}")
            self.logger.error(f"Error details: {error_details}")
            print(f"Error extracting screenshots: {str(e)}")
            print(f"Error details: {error_details}")
            raise

    def _extract_clips(self, video_path: str, markers: List[MediaMarker]) -> None:
        """Extract all video clips."""
        try:
            for i, marker in enumerate(markers):
                self.logger.info(f"Extracting clip {i + 1} at {marker.timestamp}s with duration {marker.duration}s...")
                print(f"Extracting clip {i + 1} at {marker.timestamp}s with duration {marker.duration}s...")

                # Validate inputs before extraction
                if not isinstance(marker.timestamp, (int, float)):
                    self.logger.error(f"  Invalid timestamp type: {type(marker.timestamp)}")
                    print(f"  Error: Invalid timestamp type: {type(marker.timestamp)}")
                    continue

                if not isinstance(marker.duration, (int, float)):
                    self.logger.error(f"  Invalid duration type: {type(marker.duration)}")
                    print(f"  Error: Invalid duration type: {type(marker.duration)}")
                    continue

                try:
                    output_path = extract_video_clip(
                        video_path,
                        self.output_dir,
                        marker.timestamp,
                        marker.duration
                    )
                    self.extracted_files['clips'].append(output_path)
                    self.logger.info(f"  Successfully extracted clip to: {output_path}")
                    print(f"  Successfully extracted clip to: {output_path}")
                except Exception as clip_error:
                    error_details = traceback.format_exc()
                    self.logger.error(f"  Error extracting clip {i + 1}: {str(clip_error)}")
                    self.logger.error(f"  Error details: {error_details}")
                    print(f"  Error extracting clip {i + 1}: {str(clip_error)}")
                    print(f"  Error details: {error_details}")
                    raise

        except Exception as e:
            error_details = traceback.format_exc()
            self.logger.error(f"Error extracting clips: {str(e)}")
            self.logger.error(f"Error details: {error_details}")
            print(f"Error extracting clips: {str(e)}")
            print(f"Error details: {error_details}")
            raise

    def get_media_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of extracted media files."""
        return self.extracted_files

    def cleanup_failed_extractions(self) -> None:
        """Clean up any partially extracted files in case of failure."""
        try:
            for file_type in self.extracted_files:
                for filepath in self.extracted_files[file_type]:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                self.extracted_files[file_type] = []
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")