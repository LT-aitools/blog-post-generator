import pytest
import os
from src.screenshot_extractor import extract_screenshots_at_times
from src.utils import validate_timestamps


def time_to_seconds(minutes, seconds):
    """Convert minutes and seconds to total seconds"""
    return minutes * 60 + seconds


def test_validate_timestamps():
    # Valid timestamps
    validate_timestamps([0, 10, 20])
    validate_timestamps([time_to_seconds(1, 30), time_to_seconds(2, 0)])  # 1:30 and 2:00

    # Invalid timestamps
    with pytest.raises(ValueError):
        validate_timestamps([])  # Empty list

    with pytest.raises(ValueError):
        validate_timestamps([-1, 0, 10])  # Negative timestamp

    with pytest.raises(ValueError):
        validate_timestamps([time_to_seconds(1, 0), time_to_seconds(1, 0)])  # Duplicate timestamps


def test_extract_screenshots(tmp_path):
    # Test with non-existent video file
    video_path = "nonexistent_video.mp4"
    timestamps = [time_to_seconds(0, 5), time_to_seconds(0, 10)]  # 5 and 10 seconds
    output_dir = str(tmp_path / "screenshots")

    with pytest.raises(FileNotFoundError):
        extract_screenshots_at_times(video_path, output_dir, timestamps)


def test_time_to_seconds():
    assert time_to_seconds(0, 30) == 30
    assert time_to_seconds(1, 0) == 60
    assert time_to_seconds(1, 30) == 90
    assert time_to_seconds(2, 15) == 135