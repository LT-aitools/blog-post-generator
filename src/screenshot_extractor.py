import cv2
import os
from datetime import timedelta
from .utils import validate_timestamps


def extract_screenshots_at_times(video_path, output_dir, timestamps):
    """
    Extract screenshots from a video file at specific timestamps.

    Parameters:
    video_path (str): Path to the video file
    output_dir (str): Directory to save the screenshots
    timestamps (list): List of timestamps in seconds where screenshots should be taken
    """
    # Validate inputs
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Allow duplicate timestamps - this is the key change
    validate_timestamps(timestamps, allow_duplicates=True)

    # Get video filename without extension for naming
    video_filename = os.path.splitext(os.path.basename(video_path))[0]

    # Create video-specific subfolder within output directory
    video_output_dir = os.path.join(output_dir, video_filename)
    os.makedirs(video_output_dir, exist_ok=True)

    # Open the video file
    video = cv2.VideoCapture(video_path)

    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / fps

    print(f"Video duration: {timedelta(seconds=int(duration))}")
    print(f"Saving screenshots to: {video_output_dir}")

    # Extract and save screenshots
    for i, timestamp in enumerate(timestamps):
        # Validate timestamp against video duration
        if timestamp > duration:
            print(f"Warning: Timestamp {timestamp}s exceeds video duration {duration}s")
            continue

        # Convert timestamp to frame number
        frame_idx = int(timestamp * fps)

        # Set frame position
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = video.read()

        if ret:
            # Format timestamp as HH:MM:SS
            time_str = str(timedelta(seconds=int(timestamp)))

            # Save frame with video name included in filename
            filename = f"{video_filename}_screenshot_{i + 1:03d}_at_{time_str.replace(':', '-')}.jpg"
            output_path = os.path.join(video_output_dir, filename)
            cv2.imwrite(output_path, frame)

            print(f"Saved {filename}")
        else:
            print(f"Failed to extract screenshot at {time_str}")

    # Release video capture
    video.release()