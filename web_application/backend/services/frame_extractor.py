"""
Extracts N frames at equal time intervals from a local video file using OpenCV.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List

from config import FRAMES_TO_SAMPLE


def extract_frames(video_path: str, n: int = FRAMES_TO_SAMPLE) -> List[np.ndarray]:
    """
    Seek to N evenly-spaced frame indices and return them as BGR numpy arrays.

    Args:
        video_path: Absolute path to the video file.
        n:          Number of frames to extract.

    Returns:
        List of BGR frames (numpy arrays). May be fewer than n if the video
        is shorter or some seeks fail.

    Raises:
        FileNotFoundError: If video_path does not exist.
        RuntimeError:      If OpenCV cannot open the file.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        raise RuntimeError(f"Video has no frames: {video_path}")

    actual_n = min(n, total_frames)
    step = max(total_frames // actual_n, 1)
    indices = [i * step for i in range(actual_n)]

    frames: List[np.ndarray] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret and frame is not None:
            frames.append(frame)

    cap.release()
    return frames
