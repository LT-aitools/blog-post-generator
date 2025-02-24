import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.videoclipper import extract_video_clip


def time_to_seconds(minutes, seconds):
    """Convert minutes and seconds to total seconds"""
    return minutes * 60 + seconds


def main():
    # Change the video filename here for different videos
    video_filename = "test_short.mp4"

    # Get the user's home directory and construct path to Downloads
    home_dir = os.path.expanduser("~")
    video_path = os.path.join(home_dir, "Downloads", video_filename)

    # Clips will be saved in a 'clips' directory in the project
    output_dir = "../clips"

    # Specify start time and duration
    start_time = time_to_seconds(0, 30)  # Start at 1 minute 30 seconds
    duration = time_to_seconds(0, 15)  # Clip duration: 30 seconds

    try:
        print(f"Attempting to read video from: {video_path}")
        print(f"Extracting clip starting at {start_time // 60}min {start_time % 60}sec")
        print(f"Clip duration: {duration // 60}min {duration % 60}sec")

        extract_video_clip(video_path, output_dir, start_time, duration)
        print("Clip extracted successfully!")

    except FileNotFoundError:
        print(f"Error: Could not find video file: {video_path}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    main()