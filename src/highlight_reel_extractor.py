import re
import os
import ffmpeg  # Add this
import tempfile  # Add this
from typing import List
from dataclasses import dataclass
from datetime import timedelta
from src.utils import validate_timestamps

@dataclass
class VideoSegment:
    """Represents a segment of video to include in the highlight reel."""
    start_time: int  # Start time in seconds
    duration: int  # Duration in seconds
    title: str  # Title or name of the segment
    description: str  # Optional description


def parse_timestamp(timestamp_str: str) -> int:
    """
    Parse timestamp strings in various formats into seconds.
    Supports formats: HH:MM:SS, MM:SS, or raw seconds.

    Args:
        timestamp_str: String representation of a timestamp

    Returns:
        Integer representing seconds
    """
    # Remove any leading/trailing whitespace
    timestamp_str = timestamp_str.strip()

    # Check if it's already a number
    if timestamp_str.isdigit():
        return int(timestamp_str)

    # Parse HH:MM:SS or MM:SS format
    parts = timestamp_str.split(':')

    if len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:  # MM:SS
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}")


def parse_duration(duration_str: str) -> int:
    """
    Parse duration strings into seconds.
    Supports formats like "01:30" or "(01:30)" or "(1 minute 30 seconds)".

    Args:
        duration_str: String representation of duration

    Returns:
        Integer representing seconds
    """
    # Remove parentheses if present
    duration_str = duration_str.strip().strip('()')

    # Check if it's in MM:SS format
    if ':' in duration_str:
        parts = duration_str.split(':')
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
        return minutes * 60 + seconds

    # Check if it's in "X minutes" or "X minutes Y seconds" format
    minutes_match = re.search(r'(\d+)\s*minute', duration_str)
    seconds_match = re.search(r'(\d+)\s*second', duration_str)

    minutes = int(minutes_match.group(1)) if minutes_match else 0
    seconds = int(seconds_match.group(1)) if seconds_match else 0

    return minutes * 60 + seconds


def parse_pasted_segments(text_content: str) -> List[VideoSegment]:
    """
    Parse segments from a pasted text in the format:
    Segment 1: [Title] ([duration]) **STARTING TIMESTAMP:** [HH:MM:SS] **CONTENT DESCRIPTION:** [Description]

    Args:
        text_content: The pasted text content

    Returns:
        List of VideoSegment objects
    """
    segments = []

    # Normalize line breaks and whitespace
    text_content = text_content.replace('\r\n', '\n').replace('\r', '\n')

    # Split by "Segment X:" pattern to get individual segment texts
    segment_pattern = r'Segment\s+\d+:\s+'
    segment_texts = re.split(segment_pattern, text_content)

    # Skip the first split result if it's empty (usually the case)
    if segment_texts and not segment_texts[0].strip():
        segment_texts = segment_texts[1:]

    print(f"Found {len(segment_texts)} segment texts to parse")

    for i, segment_text in enumerate(segment_texts):
        try:
            # Extract title and duration
            title_duration_pattern = r'(.+?)\s*\(([^)]+)\)'
            title_match = re.search(title_duration_pattern, segment_text)

            if not title_match:
                print(f"No title/duration match in segment {i + 1}")
                continue

            title = title_match.group(1).strip()
            duration_str = title_match.group(2).strip()

            # Extract timestamp
            timestamp_pattern = r'\*\*STARTING TIMESTAMP:\*\*\s*(\d+:\d+:\d+)'
            timestamp_match = re.search(timestamp_pattern, segment_text)

            if not timestamp_match:
                print(f"No timestamp match in segment {i + 1}")
                continue

            timestamp_str = timestamp_match.group(1).strip()

            # Extract description (optional)
            description = ""
            desc_pattern = r'\*\*CONTENT DESCRIPTION:\*\*\s*(.+?)(?=Segment\s+\d+:|$)'
            desc_match = re.search(desc_pattern, segment_text, re.DOTALL)

            if desc_match:
                description = desc_match.group(1).strip()

            # Parse duration and timestamp
            try:
                duration = parse_duration(duration_str)
                start_time = parse_timestamp(timestamp_str)

                # Create segment
                segments.append(VideoSegment(
                    start_time=start_time,
                    duration=duration,
                    title=title,
                    description=description
                ))

                print(f"Parsed segment {i + 1}: {title}, start={timestamp_str}, duration={duration_str}")

            except Exception as e:
                print(f"Error parsing values for segment {i + 1}: {str(e)}")

        except Exception as e:
            print(f"Error processing segment {i + 1}: {str(e)}")

    return segments


def extract_segments_from_text(text_content: str) -> List[VideoSegment]:
    """
    Extract video segment information from a text file.
    Supports multiple formats including the new pasted segment format.

    Args:
        text_content: Content of the text file with segment specifications

    Returns:
        List of VideoSegment objects
    """
    # Print first 200 chars to help with debugging
    print(f"Analyzing text content (first 200 chars): {text_content[:200]}...")

    # Check if we have the standard "Segment X:" format with STARTING TIMESTAMP
    if "Segment" in text_content and "**STARTING TIMESTAMP:**" in text_content:
        # This appears to be the pasted format - try the new parser first
        segments = parse_pasted_segments(text_content)
        if segments:
            return segments

    # Check if we have the custom format with "Segment X:" pattern
    if re.search(r'Segment \d+:', text_content):
        return _extract_custom_segments(text_content)

    # Try the original formats (simple format with distinct sections or markdown format)
    # Split content into lines
    segments = []
    lines = text_content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Try the simple format first: SEGMENT: Title | TIME: 00:00:00 | DURATION: X minutes
        if line.upper().startswith('SEGMENT:') or line.upper().startswith('TITLE:'):
            try:
                # Try to find all parts on one line with pipe separators
                parts = line.split('|')

                # If not split by pipes, look for the next lines
                if len(parts) == 1:
                    title_part = parts[0].strip()

                    # Look for time on next line
                    if i + 1 < len(lines) and (lines[i + 1].upper().strip().startswith('TIME:') or
                                               lines[i + 1].upper().strip().startswith('TIMESTAMP:')):
                        time_part = lines[i + 1].strip()
                        i += 1
                    else:
                        print("No time found after segment title")
                        i += 1
                        continue

                    # Look for duration on next line
                    if i + 1 < len(lines) and lines[i + 1].upper().strip().startswith('DURATION:'):
                        duration_part = lines[i + 1].strip()
                        i += 1
                    else:
                        # Default duration
                        duration_part = "DURATION: 2 minutes"
                else:
                    # All parts on one line
                    title_part = parts[0].strip()

                    # Find time part
                    time_part = next((p for p in parts if p.upper().strip().startswith('TIME:') or
                                      p.upper().strip().startswith('TIMESTAMP:')), "")

                    # Find duration part
                    duration_part = next((p for p in parts if p.upper().strip().startswith('DURATION:')),
                                         "DURATION: 2 minutes")

                # Extract title
                title = title_part.split(':', 1)[1].strip() if ':' in title_part else title_part.strip()

                # Extract timestamp
                time_value = ""
                if ':' in time_part:
                    time_value = time_part.split(':', 1)[1].strip()

                # Extract duration
                duration_value = "2 minutes"  # Default
                if ':' in duration_part:
                    duration_value = duration_part.split(':', 1)[1].strip()

                # Parse timestamp
                timestamp = parse_timestamp(time_value)

                # Parse duration
                duration_match = re.search(r'(\d+)\s*minutes?', duration_value)
                if duration_match:
                    duration = int(duration_match.group(1)) * 60
                else:
                    # Try to parse as seconds
                    try:
                        duration = int(duration_value.strip())
                    except ValueError:
                        duration = 120  # Default 2 minutes

                # Collect description from subsequent lines until empty line
                description_lines = []
                j = i + 1
                while j < len(lines) and lines[j].strip() and not any(
                        lines[j].upper().strip().startswith(prefix) for prefix in
                        ('SEGMENT:', 'TITLE:', 'TIME:', 'TIMESTAMP:', 'DURATION:')):
                    description_lines.append(lines[j].strip())
                    j += 1

                i = j if j > i + 1 else i + 1

                # Create segment
                segments.append(VideoSegment(
                    start_time=timestamp,
                    duration=duration,
                    title=title,
                    description='\n'.join(description_lines)
                ))
                print(f"Found segment (simple format): {title} at {timestamp}s for {duration}s")

            except Exception as e:
                print(f"Error parsing segment in simple format: {e}")
                i += 1

        # Try original markdown format with #### headers
        elif line.startswith('####'):
            try:
                # Start a new segment
                current_title = line.replace('####', '').strip()
                current_timestamp = None
                current_duration = None
                current_description = []

                # Extract duration if present in the title
                duration_match = re.search(r'\((\d+)\s*minutes?\)', current_title)
                if duration_match:
                    # Convert minutes to seconds
                    current_duration = int(duration_match.group(1)) * 60
                    print(f"  Duration: {current_duration}s")
                else:
                    current_duration = 120  # Default 2 minutes

                # Look for timestamp in next lines
                j = i + 1
                while j < len(lines) and lines[j].strip():
                    if lines[j].strip().startswith('STARTING TIMESTAMP:'):
                        ts_value = lines[j].replace('STARTING TIMESTAMP:', '').strip()
                        try:
                            current_timestamp = parse_timestamp(ts_value)
                            print(f"  Timestamp: {current_timestamp}s from '{ts_value}'")
                        except ValueError as e:
                            print(f"  Error parsing timestamp '{ts_value}': {e}")
                    else:
                        # Add to description
                        current_description.append(lines[j].strip())
                    j += 1

                i = j if j > i + 1 else i + 1

                # Check if we have the required information
                if current_timestamp is not None:
                    segments.append(VideoSegment(
                        start_time=current_timestamp,
                        duration=current_duration,
                        title=current_title,
                        description='\n'.join(current_description)
                    ))
                    print(f"Found segment (markdown): {current_title} at {current_timestamp}s for {current_duration}s")
                else:
                    print(f"No timestamp found for segment: {current_title}")

            except Exception as e:
                print(f"Error parsing segment in markdown format: {e}")
                i += 1
        else:
            # Skip line
            i += 1

    print(f"Total segments found: {len(segments)}")
    return segments


def _extract_custom_segments(text_content: str) -> List[VideoSegment]:
    """
    Extract video segment information from the custom format:
    Segment X: Title (duration)
    **STARTING TIMESTAMP:** HH:MM:SS **CONTENT DESCRIPTION:** Description...

    Args:
        text_content: Content of the text file with segment specifications

    Returns:
        List of VideoSegment objects
    """
    segments = []

    # Split content into lines
    lines = text_content.splitlines()

    # Variables to track current segment being parsed
    current_title = None
    current_duration = None
    current_timestamp = None
    current_description = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Check if this line contains a segment title and duration
        if line.startswith("Segment ") and "(" in line and ")" in line:
            # If we were already parsing a segment, add it to the list
            if current_title and current_timestamp:
                segments.append(VideoSegment(
                    start_time=current_timestamp,
                    duration=current_duration or 120,  # Default 2 minutes if not specified
                    title=current_title,
                    description="\n".join(current_description)
                ))
                current_description = []

            # Extract title and duration
            title_duration_pattern = r"Segment \d+: (.*?) \(([^)]+)\)"
            match = re.search(title_duration_pattern, line)
            if match:
                current_title = match.group(1).strip()
                duration_str = match.group(2).strip()
                current_duration = parse_duration(duration_str)
                print(f"Found segment: {current_title} with duration {current_duration}s")
            else:
                current_title = line
                current_duration = 120  # Default 2 minutes

        # Check if this line contains a timestamp
        elif "**STARTING TIMESTAMP:**" in line:
            timestamp_pattern = r"\*\*STARTING TIMESTAMP:\*\* (\d+:\d+:\d+)"
            match = re.search(timestamp_pattern, line)
            if match:
                timestamp_str = match.group(1).strip()
                current_timestamp = parse_timestamp(timestamp_str)
                print(f"  Found timestamp: {current_timestamp}s")

                # Extract description if it's on the same line
                if "**CONTENT DESCRIPTION:**" in line:
                    desc_pattern = r"\*\*CONTENT DESCRIPTION:\*\* (.*)"
                    desc_match = re.search(desc_pattern, line)
                    if desc_match:
                        current_description.append(desc_match.group(1).strip())

        # If not a title or timestamp line, it's part of the description
        elif current_title and not line.startswith("**TOTAL ESTIMATED DURATION:**"):
            current_description.append(line)

    # Don't forget to add the last segment
    if current_title and current_timestamp:
        segments.append(VideoSegment(
            start_time=current_timestamp,
            duration=current_duration or 120,
            title=current_title,
            description="\n".join(current_description)
        ))

    print(f"Total custom segments found: {len(segments)}")
    return segments


def create_highlight_reel(video_path: str, segments: List[VideoSegment], output_path: str) -> str:
    """
    Create a highlight reel by concatenating multiple video segments.

    Args:
        video_path: Path to the source video file
        segments: List of VideoSegment objects defining which parts to include
        output_path: Path where the highlight reel should be saved

    Returns:
        Path to the created highlight reel video
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create temp directory for segment files
    with tempfile.TemporaryDirectory() as temp_dir:
        segment_files = []

        # Extract each segment individually
        for i, segment in enumerate(segments):
            validate_timestamps([segment.start_time])
            if segment.duration <= 0:
                raise ValueError(f"Duration must be positive for segment {i + 1}")

            # Create a temporary file for this segment
            segment_filename = f"segment_{i + 1:03d}.mp4"
            segment_path = os.path.join(temp_dir, segment_filename)
            segment_files.append(segment_path)

            # Extract the segment using ffmpeg
            print(
                f"Extracting segment {i + 1}: {segment.title} (Start: {timedelta(seconds=segment.start_time)}, Duration: {timedelta(seconds=segment.duration)})")

            try:
                # Use copy codecs for both audio and video
                stream = ffmpeg.input(video_path, ss=segment.start_time, t=segment.duration)
                stream = ffmpeg.output(stream, segment_path, c='copy')  # Use copy for both audio and video
                ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            except ffmpeg.Error as e:
                print('stdout:', e.stdout.decode('utf8'))
                print('stderr:', e.stderr.decode('utf8'))
                raise RuntimeError(f"Error extracting segment {i + 1}: {str(e)}")

            print(f"Successfully extracted segment {i + 1}")

        # Create list file for concatenation
        list_file_path = os.path.join(temp_dir, "segments.txt")
        with open(list_file_path, 'w') as list_file:
            for segment_path in segment_files:
                # Use proper ffmpeg concat format with escaped paths
                escaped_path = segment_path.replace('\\', '\\\\').replace("'", "\\'")
                list_file.write(f"file '{escaped_path}'\n")

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Concatenate all segments using the concat demuxer
        try:
            print(f"Concatenating {len(segment_files)} segments into highlight reel...")

            # Use the right concat options for both audio and video
            concat = ffmpeg.input(list_file_path, format='concat', safe=0)
            concat = ffmpeg.output(concat, output_path, c='copy')  # Use copy for both audio and video
            ffmpeg.run(concat, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            total_duration = sum(segment.duration for segment in segments)
            print(f"Highlight reel created successfully!")
            print(f"Output: {output_path}")
            print(f"Total duration: {timedelta(seconds=total_duration)}")

            return output_path

        except ffmpeg.Error as e:
            print('stdout:', e.stdout.decode('utf8'))
            print('stderr:', e.stderr.decode('utf8'))
            raise RuntimeError(f"Error creating highlight reel: {str(e)}")