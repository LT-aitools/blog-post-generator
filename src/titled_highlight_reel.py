# Complete replacement for src/titled_highlight_reel.py
# This fixes all potential audio issues in the highlight reel processing

import os
import sys
import tempfile
import subprocess
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import timedelta


@dataclass
class HighlightSegment:
    """Represents a segment to include in the highlight reel with a title card."""
    title: str  # Title to display on the title card
    start_time: int  # Start time in seconds for the video clip
    duration: int  # Duration in seconds for the video clip


class TitledHighlightReel:
    """
    Creates a highlight reel with title cards shown before each video segment.

    This is a standalone implementation that uses FFmpeg directly through subprocess
    rather than relying on other modules.
    """

    def __init__(self,
                 title_duration: int = 2,
                 title_bg_color: str = "black",
                 title_text_color: str = "white",
                 title_font_size: int = 48):
        """
        Initialize the highlight reel processor.

        Args:
            title_duration: Duration in seconds to show the title card
            title_bg_color: Background color for title cards
            title_text_color: Text color for titles
            title_font_size: Font size for title text
        """
        self.title_duration = title_duration
        self.title_bg_color = title_bg_color
        self.title_text_color = title_text_color
        self.title_font_size = title_font_size

        # Check if FFmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise RuntimeError("FFmpeg is not installed or not available in the system PATH. "
                               "Please install FFmpeg to use this tool.")

    def _create_title_card(self, title: str, duration: int,
                           output_path: str, width: int = 1280, height: int = 720) -> str:
        """
        Create a title card video with the specified text.

        Args:
            title: Text to display on the card
            duration: Duration in seconds
            output_path: Where to save the title video
            width: Width of the video
            height: Height of the video

        Returns:
            Path to the created title video
        """
        # Escape special characters in title text for FFmpeg
        escaped_title = title.replace("'", "'\\''")

        # Create a title card using FFmpeg with drawtext filter
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-f', 'lavfi',
            '-i', f"color={self.title_bg_color}:s={width}x{height}:d={duration}:r=30",
            # Add silent audio to ensure audio stream exists
            '-f', 'lavfi',
            '-i', f"anullsrc=channel_layout=stereo:sample_rate=44100:d={duration}",
            '-vf', f"drawtext=text='{escaped_title}':fontcolor={self.title_text_color}:"
                   f"fontsize={self.title_font_size}:x=(w-text_w)/2:y=(h-text_h)/2",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-shortest',
            output_path
        ]

        subprocess.run(command, check=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

        return output_path

    def _extract_video_segment(self, video_path: str, start_time: int,
                               duration: int, output_path: str) -> str:
        """
        Extract a segment from the source video.

        Args:
            video_path: Path to the source video
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Where to save the segment

        Returns:
            Path to the extracted segment
        """
        # The key to fixing audio issues is to use the right seekng method
        # Using -ss before -i for fast seeking, but might have issue with some files
        # So we include a fallback method that will be executed if the first method fails
        try:
            # Method 1: Faster seeking (ss before input)
            command = [
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-ss', str(start_time),
                '-i', video_path,
                '-t', str(duration),
                '-c:v', 'libx264',  # Re-encode to ensure consistent format
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-strict', 'experimental',
                output_path
            ]

            result = subprocess.run(command, check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)

            # Check if there's audio in the output
            probe_command = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'stream=codec_type',
                '-of', 'csv=p=0',
                output_path
            ]

            probe_result = subprocess.run(probe_command, check=True,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=True)

            # If no audio is found, try the alternative method
            if 'audio' not in probe_result.stdout:
                raise subprocess.SubprocessError("No audio stream detected in output")

            return output_path

        except (subprocess.SubprocessError, subprocess.CalledProcessError):
            print("First extraction method failed, trying alternative method...")

            # Method 2: More accurate seeking (ss after input)
            command = [
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'libx264',  # Re-encode to ensure consistent format
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-strict', 'experimental',
                output_path
            ]

            subprocess.run(command, check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

            return output_path

    def _get_video_properties(self, video_path: str) -> Tuple[int, int, int]:
        """
        Get video width, height, and framerate.

        Args:
            video_path: Path to the video

        Returns:
            Tuple of (width, height, framerate)
        """
        command = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate',
            '-of', 'csv=p=0',
            video_path
        ]

        result = subprocess.run(command, check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)

        width, height, frame_rate = result.stdout.strip().split(',')
        # Handle frame rate in the format num/den
        if '/' in frame_rate:
            num, den = frame_rate.split('/')
            frame_rate = int(float(num) / float(den))
        else:
            frame_rate = int(float(frame_rate))

        return int(width), int(height), frame_rate

    def _create_concat_file(self, file_list: List[str], output_path: str) -> str:
        """
        Create a concat file for FFmpeg.

        Args:
            file_list: List of files to concatenate
            output_path: Where to save the concat file

        Returns:
            Path to the concat file
        """
        with open(output_path, 'w') as f:
            for file_path in file_list:
                # Properly escape paths for ffmpeg concat format
                escaped_path = file_path.replace('\\', '\\\\').replace("'", "\\'")
                f.write(f"file '{escaped_path}'\n")

        return output_path

    def create_highlight_reel(self,
                              video_path: str,
                              segments: List[HighlightSegment],
                              output_path: str) -> str:
        """
        Create a highlight reel by adding title cards before each segment.

        Args:
            video_path: Path to the source video
            segments: List of segments to include
            output_path: Where to save the highlight reel

        Returns:
            Path to the created highlight reel
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not segments:
            raise ValueError("No segments specified for the highlight reel")

        # Get video properties
        width, height, _ = self._get_video_properties(video_path)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Create temp directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Lists to track all files for concatenation
            all_segment_files = []

            # Process each segment
            for i, segment in enumerate(segments):
                print(f"Processing segment {i + 1}: {segment.title}")

                # 1. Create title card
                title_file = os.path.join(temp_dir, f"title_{i + 1:03d}.mp4")
                self._create_title_card(
                    segment.title,
                    self.title_duration,
                    title_file,
                    width,
                    height
                )
                all_segment_files.append(title_file)

                # 2. Extract video segment
                segment_file = os.path.join(temp_dir, f"segment_{i + 1:03d}.mp4")
                try:
                    self._extract_video_segment(
                        video_path,
                        segment.start_time,
                        segment.duration,
                        segment_file
                    )
                    all_segment_files.append(segment_file)
                except subprocess.CalledProcessError as e:
                    print(f"Error extracting segment {i + 1}: {str(e)}")
                    print(f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}")
                    raise RuntimeError(f"Failed to extract segment {i + 1}")

            # Create concat file
            concat_file = os.path.join(temp_dir, "concat.txt")
            self._create_concat_file(all_segment_files, concat_file)

            # Concatenate all segments - using the concat demuxer
            try:
                print(f"Concatenating {len(all_segment_files)} clips...")

                # Use the filter_complex approach for more reliable audio handling
                inputs = []
                filter_parts = []

                for i, file in enumerate(all_segment_files):
                    inputs.extend(['-i', file])
                    filter_parts.append(f'[{i}:v:0][{i}:a:0]')

                filter_complex = ''.join(filter_parts) + f'concat=n={len(all_segment_files)}:v=1:a=1[outv][outa]'

                concat_command = [
                    'ffmpeg',
                    '-y',
                    *inputs,
                    '-filter_complex', filter_complex,
                    '-map', '[outv]',
                    '-map', '[outa]',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    output_path
                ]

                subprocess.run(concat_command, check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

                # Calculate total duration
                total_duration = sum(segment.duration for segment in segments) + (len(segments) * self.title_duration)

                print(f"Highlight reel created successfully!")
                print(f"Output: {output_path}")
                print(f"Total duration: {timedelta(seconds=total_duration)}")

                return output_path

            except subprocess.CalledProcessError as e:
                print(f"Error creating highlight reel: {str(e)}")
                print(f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}")

                # Fall back to the concat demuxer method if filter_complex fails
                try:
                    print("Trying alternative concatenation method...")

                    concat_command = [
                        'ffmpeg',
                        '-y',
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', concat_file,
                        '-c:v', 'libx264',
                        '-preset', 'fast',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        output_path
                    ]

                    subprocess.run(concat_command, check=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

                    return output_path

                except subprocess.CalledProcessError as e2:
                    print(f"Alternative method also failed: {str(e2)}")
                    print(f"Error output: {e2.stderr.decode() if e2.stderr else 'No error output'}")
                    raise RuntimeError("Failed to create highlight reel")


def create_titled_highlight_reel(
        video_path: str,
        segments: List[HighlightSegment],
        output_dir: str = "highlight_reels",
        title_duration: int = 2
) -> str:
    """
    Convenience function to create a highlight reel with title cards.

    Args:
        video_path: Path to the source video
        segments: List of segment specifications
        output_dir: Directory to save the highlight reel
        title_duration: Duration in seconds for title cards

    Returns:
        Path to the created highlight reel
    """
    # Validate video path
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create output filename
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = f"{video_filename}_titled_highlight.mp4"
    output_path = os.path.join(output_dir, output_filename)

    # Create the processor and generate the highlight reel
    processor = TitledHighlightReel(title_duration=title_duration)
    return processor.create_highlight_reel(video_path, segments, output_path)