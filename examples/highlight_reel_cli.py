import os
import sys
import argparse
import json
from pathlib import Path

# Add the project root directory to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Import the highlight reel processor
from titled_highlight_reel import HighlightSegment, create_titled_highlight_reel


def parse_time(time_str):
    """
    Parse a time string in the format of HH:MM:SS, MM:SS, or seconds.

    Args:
        time_str: A string representing time

    Returns:
        Integer seconds
    """
    time_str = time_str.strip()

    # If it's already a number, return it as seconds
    if time_str.isdigit():
        return int(time_str)

    # Process HH:MM:SS or MM:SS
    parts = time_str.split(':')

    if len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:  # MM:SS
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}. Use HH:MM:SS, MM:SS, or seconds.")


def main():
    parser = argparse.ArgumentParser(description='Create a highlight reel with title cards')

    parser.add_argument('video_path', help='Path to the source video file')

    parser.add_argument(
        '--segments', '-s',
        type=str,
        help='JSON file with segments or JSON string with segments list'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='highlight_reels',
        help='Output directory for the highlight reel (default: highlight_reels)'
    )

    parser.add_argument(
        '--title-duration', '-t',
        type=int,
        default=2,
        help='Duration in seconds to show the title card (default: 2)'
    )

    args = parser.parse_args()

    # Verify video path
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        return 1

    # Parse segments
    segments = []

    if args.segments:
        try:
            # Check if it's a file path
            if os.path.exists(args.segments):
                with open(args.segments, 'r') as f:
                    segments_data = json.load(f)
            else:
                # Assume it's a JSON string
                segments_data = json.loads(args.segments)

            # Convert to HighlightSegment objects
            for segment in segments_data:
                if isinstance(segment, dict):
                    title = segment.get('title', 'Untitled')

                    # Handle start_time as string or number
                    start_time = segment.get('start_time', 0)
                    if isinstance(start_time, str):
                        start_time = parse_time(start_time)

                    # Handle duration as string or number
                    duration = segment.get('duration', 30)
                    if isinstance(duration, str):
                        duration = parse_time(duration)

                    segments.append(HighlightSegment(
                        title=title,
                        start_time=start_time,
                        duration=duration
                    ))
        except Exception as e:
            print(f"Error parsing segments: {str(e)}")
            print("Segments should be a JSON array with objects containing title, start_time, and duration.")
            print("Example: [{\"title\": \"Intro\", \"start_time\": \"00:01:30\", \"duration\": 120}]")
            return 1

    # If no segments provided, enter interactive mode
    if not segments:
        print("No segments provided. Entering interactive mode.")
        print("Enter details for each segment (leave title blank to finish):")

        segment_num = 1
        while True:
            print(f"\nSegment {segment_num}:")
            title = input("  Title: ").strip()
            if not title:
                break

            while True:
                try:
                    start_time_str = input("  Start Time (HH:MM:SS or MM:SS): ").strip()
                    start_time = parse_time(start_time_str)
                    break
                except ValueError as e:
                    print(f"  Error: {str(e)}")

            while True:
                try:
                    duration_str = input("  Duration (seconds or MM:SS): ").strip()
                    duration = parse_time(duration_str)
                    break
                except ValueError as e:
                    print(f"  Error: {str(e)}")

            segments.append(HighlightSegment(
                title=title,
                start_time=start_time,
                duration=duration
            ))

            segment_num += 1

    # Create highlight reel
    if not segments:
        print("No segments defined. Exiting.")
        return 1

    print(f"Creating highlight reel with {len(segments)} segments...")
    for i, segment in enumerate(segments):
        print(f"  Segment {i + 1}: {segment.title} - Start: {segment.start_time}s, Duration: {segment.duration}s")

    try:
        output_path = create_titled_highlight_reel(
            args.video_path,
            segments,
            args.output,
            args.title_duration
        )
        print(f"Highlight reel created successfully at: {output_path}")
        return 0
    except Exception as e:
        print(f"Error creating highlight reel: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())