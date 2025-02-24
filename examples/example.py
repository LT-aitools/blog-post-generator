import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.screenshot_extractor import extract_screenshots_at_times


def time_to_seconds(minutes, seconds):
    """Convert minutes and seconds to total seconds"""
    return minutes * 60 + seconds


def main():
    # Change the video filename here for different videos
    video_filename = "test_short.mp4"  # Example: "my_video.mp4"

    # Get the user's home directory and construct path to Downloads
    home_dir = os.path.expanduser("~")
    video_path = os.path.join(home_dir, "Downloads", video_filename)

    # Screenshots will be saved in a 'screenshots' directory in the project
    output_dir = "../screenshots"

    # Specify timestamps as (minutes, seconds)
    # Example: time_to_seconds(1, 30) means 1 minute and 30 seconds
    timestamps = [
        time_to_seconds(0, 5),  # 0 min 5 sec
        time_to_seconds(0, 15),  # 1 min 30 sec
        time_to_seconds(0, 30)  # 2 min 15 sec
    ]

    try:
        print(f"Attempting to read video from: {video_path}")
        print("Taking screenshots at:")
        for t in timestamps:
            minutes = t // 60
            seconds = t % 60
            print(f"  {minutes}min {seconds}sec")

        extract_screenshots_at_times(video_path, output_dir, timestamps)
        print("Screenshots extracted successfully!")
        print(f"Screenshots saved in: {os.path.abspath(output_dir)}")
    except FileNotFoundError:
        print(f"Error: Could not find video file: {video_path}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    main()