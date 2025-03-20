import logging
import re
from dataclasses import dataclass
from typing import List, Tuple
from docx import Document


@dataclass
class MediaMarker:
    """Represents a media marker in the blog text."""
    type: str  # 'CLIP' or 'SCREENSHOT'
    timestamp: int
    duration: int = None
    align: str = 'center'
    caption: str = ''
    original_text: str = ''


class BlogDocumentReader:
    """Reads and parses blog posts from Word documents or text files, extracting media markers."""

    def __init__(self):
        self.logger = logging.getLogger("BlogDocumentReader")
        self.logger.setLevel(logging.INFO)

        # Add a console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

        # Simple regex patterns for media markers
        self.clip_pattern = r'\[CLIP\s+timestamp="([^"]+)"\s+duration="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'
        self.screenshot_pattern = r'\[SCREENSHOT\s+timestamp="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'

        # Additional patterns for capturing markers without align parameter
        self.clip_pattern_no_align = r'\[CLIP\s+timestamp="([^"]+)"\s+duration="([^"]+)"\]([^\[]*)'
        self.screenshot_pattern_no_align = r'\[SCREENSHOT\s+timestamp="([^"]+)"\]([^\[]*)'

    def parse_time(self, time_str: str) -> int:
        """Convert time string (e.g., '1:30', '00:01:30', or '4119.6') to seconds."""
        try:
            # Handle decimal timestamps (e.g., "4119.6")
            if '.' in time_str:
                return int(float(time_str))
            
            # Handle HH:MM:SS or MM:SS format
            parts = time_str.strip().split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            
            # Handle plain seconds
            return int(time_str)
        except ValueError as e:
            self.logger.error(f"Error parsing time '{time_str}': {str(e)}")
            raise

    def _process_clip_markers(self, text: str, markers: List[MediaMarker], para_num: int):
        """Process clip markers in text."""
        # Try pattern with align first
        matches = re.finditer(self.clip_pattern, text)
        for match in matches:
            timestamp = self.parse_time(match.group(1))
            duration = int(match.group(2))
            align = match.group(3)
            caption = match.group(4).strip()
            markers.append(MediaMarker(
                type='CLIP',
                timestamp=timestamp,
                duration=duration,
                align=align,
                caption=caption,
                original_text=match.group(0)
            ))
            self.logger.info(f"Found CLIP marker with align - timestamp: {timestamp}, duration: {duration}, align: {align}")

        # Try pattern without align
        matches = re.finditer(self.clip_pattern_no_align, text)
        for match in matches:
            timestamp = self.parse_time(match.group(1))
            duration = int(match.group(2))
            caption = match.group(3).strip()
            markers.append(MediaMarker(
                type='CLIP',
                timestamp=timestamp,
                duration=duration,
                align='center',  # Default to center
                caption=caption,
                original_text=match.group(0)
            ))
            self.logger.info(f"Found CLIP marker (no align) - timestamp: {timestamp}, duration: {duration}")

    def _process_screenshot_markers(self, text: str, markers: List[MediaMarker], para_num: int):
        """Process screenshot markers in text."""
        # Try pattern with align first
        matches = re.finditer(self.screenshot_pattern, text)
        for match in matches:
            timestamp = self.parse_time(match.group(1))
            align = match.group(2)
            caption = match.group(3).strip()
            markers.append(MediaMarker(
                type='SCREENSHOT',
                timestamp=timestamp,
                align=align,
                caption=caption,
                original_text=match.group(0)
            ))
            self.logger.info(f"Found SCREENSHOT marker with align - timestamp: {timestamp}, align: {align}")

        # Try pattern without align
        matches = re.finditer(self.screenshot_pattern_no_align, text)
        for match in matches:
            timestamp = self.parse_time(match.group(1))
            caption = match.group(2).strip()
            markers.append(MediaMarker(
                type='SCREENSHOT',
                timestamp=timestamp,
                align='center',  # Default to center
                caption=caption,
                original_text=match.group(0)
            ))
            self.logger.info(f"Found SCREENSHOT marker (no align) - timestamp: {timestamp}")

    def extract_markers(self, doc_path: str) -> Tuple[List[MediaMarker], str]:
        """Extract media markers from Word document or text file."""
        self.logger.info(f"Reading document: {doc_path}")
        
        # Check file extension
        if doc_path.lower().endswith('.txt'):
            # Handle text file
            with open(doc_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            # Handle Word document
            doc = Document(doc_path)
            lines = [para.text for para in doc.paragraphs]

        full_text = []
        markers = []

        # Process each line/paragraph
        for i, line in enumerate(lines, 1):
            text = line.strip()
            if not text:
                full_text.append('')
                continue

            # Debug log the text we're processing
            self.logger.info(f"Processing paragraph {i}:")
            self.logger.info(f"Text: {text}")

            # Process both types of patterns for each marker type
            self._process_clip_markers(text, markers, i)
            self._process_screenshot_markers(text, markers, i)

            full_text.append(text)

        self.logger.info(f"Total markers found: {len(markers)}")
        for i, marker in enumerate(markers, 1):
            self.logger.info(f"Marker {i}: {marker.type} at {marker.timestamp}s")

        return markers, '\n'.join(full_text)

    def validate_markers(self, markers: List[MediaMarker]) -> List[str]:
        """Validate the extracted markers."""
        warnings = []
        
        # Check for duplicate timestamps within each marker type
        timestamps_by_type = {}
        for marker in markers:
            if marker.type not in timestamps_by_type:
                timestamps_by_type[marker.type] = {}
            if marker.timestamp in timestamps_by_type[marker.type]:
                warnings.append(f"Duplicate timestamp {marker.timestamp}s found for {marker.type} markers")
            timestamps_by_type[marker.type][marker.timestamp] = marker

        return warnings