import re
import logging
from dataclasses import dataclass
from typing import List, Optional
from docx import Document


@dataclass
class MediaMarker:
    type: str  # 'CLIP' or 'SCREENSHOT'
    timestamp: str
    duration: Optional[str]
    align: str
    caption: str
    original_text: str


class BlogDocumentReader:
    """Reads and parses blog posts from Word documents, extracting media markers."""

    def __init__(self):
        self.logger = logging.getLogger("BlogDocumentReader")
        self.logger.setLevel(logging.INFO)

        # Add a console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

        # More forgiving regex patterns
        self.clip_pattern = r'\[CLIP\s+timestamp="([^"]+)"\s+duration="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'
        self.screenshot_pattern = r'\[SCREENSHOT\s+timestamp="([^"]+)"\s+align\s*[="]*([^"\]\s]+)["]?\]([^\[]*)'

    def parse_time(self, time_str: str) -> int:
        """Convert time string (e.g., '1:30' or '00:01:30') to seconds."""
        try:
            parts = time_str.strip().split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            return int(time_str)
        except ValueError as e:
            self.logger.error(f"Error parsing time '{time_str}': {str(e)}")
            raise

    def extract_markers(self, doc_path: str) -> tuple[List[MediaMarker], str]:
        """Extract media markers from Word document."""
        self.logger.info(f"Reading document: {doc_path}")
        doc = Document(doc_path)
        full_text = []
        markers = []

        # Process each paragraph
        for i, para in enumerate(doc.paragraphs, 1):
            text = para.text.strip()
            if not text:
                full_text.append('')
                continue

            # Debug log the text we're processing
            self.logger.info(f"Processing paragraph {i}:")
            self.logger.info(f"Text: {text}")

            # Look for clip markers
            clip_matches = list(re.finditer(self.clip_pattern, text))
            if clip_matches:
                self.logger.info(f"Found {len(clip_matches)} clip markers in paragraph {i}")

            for match in clip_matches:
                try:
                    timestamp, duration, align, caption = match.groups()
                    self.logger.info(
                        f"Found CLIP marker - timestamp: {timestamp}, duration: {duration}, align: {align}")

                    # Clean up align value
                    align = align.strip('"').strip()

                    markers.append(MediaMarker(
                        type='CLIP',
                        timestamp=self.parse_time(timestamp),
                        duration=self.parse_time(duration),
                        align=align,
                        caption=caption.strip(),
                        original_text=match.group(0)
                    ))
                except Exception as e:
                    self.logger.error(f"Error processing clip marker: {str(e)}")
                    self.logger.error(f"Marker text: {match.group(0)}")

            # Look for screenshot markers
            screenshot_matches = list(re.finditer(self.screenshot_pattern, text))
            if screenshot_matches:
                self.logger.info(f"Found {len(screenshot_matches)} screenshot markers in paragraph {i}")

            for match in screenshot_matches:
                try:
                    timestamp, align, caption = match.groups()
                    self.logger.info(f"Found SCREENSHOT marker - timestamp: {timestamp}, align: {align}")

                    # Clean up align value
                    align = align.strip('"').strip()

                    markers.append(MediaMarker(
                        type='SCREENSHOT',
                        timestamp=self.parse_time(timestamp),
                        duration=None,
                        align=align,
                        caption=caption.strip(),
                        original_text=match.group(0)
                    ))
                except Exception as e:
                    self.logger.error(f"Error processing screenshot marker: {str(e)}")
                    self.logger.error(f"Marker text: {match.group(0)}")

            full_text.append(text)

        self.logger.info(f"Total markers found: {len(markers)}")
        for i, marker in enumerate(markers, 1):
            self.logger.info(f"Marker {i}: {marker.type} at {marker.timestamp}s")

        return markers, '\n'.join(full_text)

    def validate_markers(self, markers: List[MediaMarker]) -> List[str]:
        """Validate the extracted markers for potential issues."""
        warnings = []

        for i, marker in enumerate(markers, 1):
            if marker.type == 'CLIP' and marker.duration < 1:
                warnings.append(f"Warning: Clip #{i} has duration less than 1 second")

            # Add timestamp validation
            try:
                if isinstance(marker.timestamp, str):
                    self.parse_time(marker.timestamp)
            except ValueError:
                warnings.append(f"Warning: Invalid timestamp format in marker #{i}")

        return warnings