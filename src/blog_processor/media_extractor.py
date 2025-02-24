import os
import logging
from typing import List, Dict
from pathlib import Path
from datetime import datetime, timedelta

# Import video utilities
from ..videoclipper import extract_video_clip
from ..screenshot_extractor import extract_screenshots_at_times
from .docx_reader import MediaMarker


class MediaExtractor:
    """Handles extraction and organization of media files from video."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.logger = logging.getLogger("MediaExtractor")

        # Track extracted files
        self.extracted_files: Dict[str, List[str]] = {
            'clips': [],
            'screenshots': []
        }

    def extract_all_media(self, video_path: str, markers: List[MediaMarker]) -> bool:
        """Extract all media files based on the markers."""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            os.makedirs(self.output_dir, exist_ok=True)

            # Extract screenshots first (more efficient to do in batch)
            screenshot_markers = [m for m in markers if m.type == 'SCREENSHOT']
            if screenshot_markers:
                self._extract_screenshots(video_path, screenshot_markers)

            # Extract video clips
            clip_markers = [m for m in markers if m.type == 'CLIP']
            if clip_markers:
                self._extract_clips(video_path, clip_markers)

            return True

        except Exception as e:
            self.logger.error(f"Error during media extraction: {str(e)}")
            return False

    def _extract_screenshots(self, video_path: str, markers: List[MediaMarker]) -> None:
        """Extract all screenshots in batch."""
        try:
            self.logger.info(f"Extracting {len(markers)} screenshots...")

            # Get all timestamps
            timestamps = [marker.timestamp for marker in markers]

            # Extract screenshots
            extract_screenshots_at_times(video_path, self.output_dir, timestamps)

            # Track extracted files
            for i, marker in enumerate(markers):
                time_str = str(timedelta(seconds=int(marker.timestamp))).replace(':', '-')
                filename = f"screenshot_{i + 1:03d}_at_{time_str}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                self.extracted_files['screenshots'].append(filepath)

        except Exception as e:
            self.logger.error(f"Error extracting screenshots: {str(e)}")
            raise

    def _extract_clips(self, video_path: str, markers: List[MediaMarker]) -> None:
        """Extract all video clips."""
        try:
            for i, marker in enumerate(markers):
                self.logger.info(f"Extracting clip {i + 1} at {marker.timestamp}s...")
                output_path = extract_video_clip(
                    video_path,
                    self.output_dir,
                    marker.timestamp,
                    marker.duration
                )
                self.extracted_files['clips'].append(output_path)

        except Exception as e:
            self.logger.error(f"Error extracting clips: {str(e)}")
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