import os
import re
import ffmpeg
import tempfile
from typing import List, Tuple
from dataclasses import dataclass
from datetime import timedelta
from .utils import validate_timestamps


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


def extract_segments_from_text(text_content: str) -> List[VideoSegment]:
    """
    Extract video segment information from a text file.

    Args:
        text_content: Content of the text file with segment specifications

    Returns:
        List of VideoSegment objects
    """
    segments = []

    # Print first 200 chars to help with debugging
    print(f"Analyzing text content (first 200 chars): {text_content[:200]}...")

    # Use a simpler format with distinct sections separated by blank lines
    # Look for lines with timestamp and duration in an easier format

    # Format 1: SEGMENT: Title | TIME: 00:00:00 | DURATION: 2 minutes
    # Format 2: Standard markdown format with #### headers

    # Split content into lines
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
                stream = ffmpeg.input(video_path, ss=segment.start_time, t=segment.duration)
                stream = ffmpeg.output(stream, segment_path, acodec='copy', vcodec='copy')
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
                list_file.write(f"file '{segment_path}'\n")

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Concatenate all segments using the concat demuxer
        try:
            print(f"Concatenating {len(segment_files)} segments into highlight reel...")

            concat = ffmpeg.input(list_file_path, format='concat', safe=0)
            concat = ffmpeg.output(concat, output_path, codec='copy')
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


def create_highlight_reel_from_file(video_path: str, content_file_path: str,
                                    output_dir: str = "highlight_reels") -> str:
    """
    Create a highlight reel based on segment specifications in a text file.

    Args:
        video_path: Path to the source video file
        content_file_path: Path to the text file with segment specifications
        output_dir: Directory where the highlight reel should be saved

    Returns:
        Path to the created highlight reel video
    """
    # Validate inputs
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not os.path.exists(content_file_path):
        raise FileNotFoundError(f"Content file not found: {content_file_path}")

    # Read the content file
    with open(content_file_path, 'r') as f:
        content = f.read()

    # Extract segments from the content
    segments = extract_segments_from_text(content)

    if not segments:
        raise ValueError("No valid segments found in the content file")

    # Create output filename based on video name and timestamp
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = f"{video_filename}_highlight_reel.mp4"
    output_path = os.path.join(output_dir, output_filename)

    # Create the highlight reel
    return create_highlight_reel(video_path, segments, output_path)