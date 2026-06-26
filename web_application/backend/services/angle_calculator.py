"""
Pure geometry functions for joint angle computation.
Ported from data_preprocessing.ipynb — no I/O, no MediaPipe dependency.
"""
import numpy as np


def calculate_angle(a, b, c) -> float:
    """Angle at point B formed by vectors BA and BC. Returns degrees in [0, 180]."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = (
        np.arctan2(c[1] - b[1], c[0] - b[0])
        - np.arctan2(a[1] - b[1], a[0] - b[0])
    )
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle


def calculate_shoulder_elevation(shoulder, elbow) -> float:
    """
    Angle of the upper arm relative to a vertical downward reference.
    0° = arm hanging straight down, 90° = horizontal, 180° = fully raised.
    Uses a virtual point directly below the shoulder as the reference direction.
    """
    virtual_below = [shoulder[0], shoulder[1] + 0.1]
    return calculate_angle(virtual_below, shoulder, elbow)


def calculate_body_rotation(ls_xyz, rs_xyz, lh_xyz, rh_xyz) -> float | None:
    """
    Body rotation angle (degrees) from shoulder and hip Z-depth differences.
    Returns None if insufficient landmarks are visible.
    """
    parts = []
    if ls_xyz is not None and rs_xyz is not None:
        shoulder_rot = np.arctan2(
            rs_xyz[2] - ls_xyz[2], rs_xyz[0] - ls_xyz[0]
        ) * (180 / np.pi)
        parts.append(shoulder_rot)
    if lh_xyz is not None and rh_xyz is not None:
        hip_rot = np.arctan2(
            rh_xyz[2] - lh_xyz[2], rh_xyz[0] - lh_xyz[0]
        ) * (180 / np.pi)
        parts.append(hip_rot)
    return float(np.mean(parts)) if parts else None
