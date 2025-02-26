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

    # Regular expression to find segment headers and timestamps
    segment_pattern = r'#{1,6}\s*(Segment \d+[^#]*?)(?=#{1,6}|\Z)'
    timestamp_pattern = r'STARTING TIMESTAMP:\s*([0-9:]+)'
    duration_pattern = r'\((\d+)\s*minutes?\)'

    # Find all segments in the text
    segment_matches = re.finditer(segment_pattern, text_content, re.DOTALL)

    for match in segment_matches:
        segment_text = match.group(1).strip()

        # Extract the segment title
        title_match = re.search(r'(.*?)(?:\(|$)', segment_text)
        title = title_match.group(1).strip() if title_match else "Untitled Segment"

        # Extract the timestamp
        timestamp_match = re.search(timestamp_pattern, segment_text)
        if not timestamp_match:
            print(f"Warning: No starting timestamp found for segment: {title}")
            continue

        start_timestamp = timestamp_match.group(1).strip()
        start_time = parse_timestamp(start_timestamp)

        # Extract the duration
        duration_match = re.search(duration_pattern, segment_text)
        if duration_match:
            # Convert minutes to seconds
            duration = int(duration_match.group(1)) * 60
        else:
            # Default to a 2-minute segment if duration not specified
            print(f"Warning: No duration specified for segment: {title}. Using default of 2 minutes.")
            duration = 120

        # Extract the description (everything except the title and technical details)
        lines = segment_text.split('\n')
        description_lines = []

        for line in lines:
            # Skip the title line, timestamp line, and empty lines
            if title in line or "STARTING TIMESTAMP:" in line or not line.strip():
                continue
            description_lines.append(line.strip())

        description = '\n'.join(description_lines)

        # Create and add the segment
        segments.append(VideoSegment(
            start_time=start_time,
            duration=duration,
            title=title,
            description=description
        ))

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