import ffmpeg
import os
from datetime import timedelta
from .utils import validate_timestamps


def extract_video_clip(video_path, output_dir, start_time, duration):
    """
    Extract a video clip starting at a specific timestamp for a given duration.
    Preserves both video and audio.

    Parameters:
    video_path (str): Path to the video file
    output_dir (str): Directory to save the clip
    start_time (int): Start time in seconds
    duration (int): Duration of the clip in seconds
    """
    # Validate inputs
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Allow duplicate timestamps - this is the key change
    validate_timestamps([start_time], allow_duplicates=True)
    if duration <= 0:
        raise ValueError("Duration must be positive")

    # Get video filename without extension for naming
    video_filename = os.path.splitext(os.path.basename(video_path))[0]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create output filename with timestamp information
    start_str = str(timedelta(seconds=int(start_time))).replace(':', '-')
    duration_str = str(timedelta(seconds=int(duration))).replace(':', '-')
    output_filename = f"{video_filename}_clip_from_{start_str}_duration_{duration_str}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    try:
        print("Extracting clip...")

        # Extract the clip using ffmpeg
        stream = ffmpeg.input(video_path, ss=start_time, t=duration)
        stream = ffmpeg.output(stream, output_path, acodec='copy', vcodec='copy')

        # Run the ffmpeg command
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

        print(f"Clip saved to: {output_path}")
        print(f"Duration: {duration:.1f} seconds")

    except ffmpeg.Error as e:
        print('stdout:', e.stdout.decode('utf8'))
        print('stderr:', e.stderr.decode('utf8'))
        raise RuntimeError(f"Error while extracting clip: {str(e)}")

    return output_path