def validate_timestamps(timestamps):
    """
    Validate timestamp inputs.

    Parameters:
    timestamps (list): List of timestamps in seconds

    Raises:
    ValueError: If timestamps are invalid
    """
    if not timestamps:
        raise ValueError("No timestamps provided")

    if not isinstance(timestamps, (list, tuple)):
        raise ValueError("Timestamps must be a list or tuple")

    if not all(isinstance(t, (int, float)) and t >= 0 for t in timestamps):
        raise ValueError("All timestamps must be non-negative numbers")

    if len(timestamps) != len(set(timestamps)):
        raise ValueError("Duplicate timestamps found")