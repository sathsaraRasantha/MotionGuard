"""
Runs MediaPipe Pose on a list of BGR frames and computes joint angles.
Combines keypoint extraction and angle calculation into one pass.
"""
import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import List, Optional

from config import (
    MEDIAPIPE_DETECTION_CONFIDENCE,
    MEDIAPIPE_TRACKING_CONFIDENCE,
    LANDMARK_VISIBILITY_THRESHOLD,
    BODY_ROTATION_THRESHOLD_DEG,
)
from services.angle_calculator import (
    calculate_angle,
    calculate_shoulder_elevation,
    calculate_body_rotation,
)

PL = mp.solutions.pose.PoseLandmark


@dataclass
class FrameFeatures:
    """Computed features for one video frame. Any field may be None if landmarks were not visible."""
    shoulder_angles: Optional[float]
    elbow_angles: Optional[float]
    hip_angles: Optional[float]
    knee_angles: Optional[float]
    body_angles: Optional[float]
    front_facing_boolean: Optional[int]   # 1 = front-facing, 0 = rotated

    def is_valid(self) -> bool:
        """True when the frame has at least one non-None angle (usable by classifier)."""
        return any(v is not None for v in (
            self.shoulder_angles, self.elbow_angles,
            self.hip_angles, self.knee_angles,
        ))

    def to_feature_row(self) -> Optional[List[float]]:
        """
        Returns [shoulder, elbow, hip, knee, body, front_facing] with 0.0 substituted
        for missing values, or None if the frame is entirely invalid.
        """
        if not self.is_valid():
            return None
        return [
            self.shoulder_angles or 0.0,
            self.elbow_angles or 0.0,
            self.hip_angles or 0.0,
            self.knee_angles or 0.0,
            self.body_angles or 0.0,
            float(self.front_facing_boolean) if self.front_facing_boolean is not None else 0.0,
        ]


def _get_lm(landmarks, landmark_enum, min_vis: float = LANDMARK_VISIBILITY_THRESHOLD):
    lm = landmarks[landmark_enum.value]
    return [lm.x, lm.y] if lm.visibility >= min_vis else None


def _get_lm_xyz(landmarks, landmark_enum, min_vis: float = 0.3):
    lm = landmarks[landmark_enum.value]
    return [lm.x, lm.y, lm.z] if lm.visibility >= min_vis else None


def _extract_angles(landmarks) -> FrameFeatures:
    # ── Shoulder elevation ────────────────────────────────────────────────────
    l_sh = _get_lm(landmarks, PL.LEFT_SHOULDER)
    l_el = _get_lm(landmarks, PL.LEFT_ELBOW)
    r_sh = _get_lm(landmarks, PL.RIGHT_SHOULDER)
    r_el = _get_lm(landmarks, PL.RIGHT_ELBOW)

    if l_sh and l_el:
        s_angle = calculate_shoulder_elevation(l_sh, l_el)
    elif r_sh and r_el:
        r_sh_m = [1 - r_sh[0], r_sh[1]]
        r_el_m = [1 - r_el[0], r_el[1]]
        s_angle = calculate_shoulder_elevation(r_sh_m, r_el_m)
    else:
        s_angle = None

    # ── Elbow angle (shoulder → elbow → wrist) ────────────────────────────────
    l_wr = _get_lm(landmarks, PL.LEFT_WRIST)
    if l_sh and l_el and l_wr:
        e_angle = calculate_angle(l_sh, l_el, l_wr)
    else:
        r_wr = _get_lm(landmarks, PL.RIGHT_WRIST)
        e_angle = calculate_angle(r_sh, r_el, r_wr) if (r_sh and r_el and r_wr) else None

    # ── Hip angle (shoulder → hip → knee) ─────────────────────────────────────
    l_hi = _get_lm(landmarks, PL.LEFT_HIP)
    l_kn = _get_lm(landmarks, PL.LEFT_KNEE)
    if l_sh and l_hi and l_kn:
        h_angle = calculate_angle(l_sh, l_hi, l_kn)
    else:
        r_hi = _get_lm(landmarks, PL.RIGHT_HIP)
        r_kn = _get_lm(landmarks, PL.RIGHT_KNEE)
        h_angle = calculate_angle(r_sh, r_hi, r_kn) if (r_sh and r_hi and r_kn) else None

    # ── Knee angle (hip → knee → ankle) ──────────────────────────────────────
    l_an = _get_lm(landmarks, PL.LEFT_ANKLE)
    if l_hi and l_kn and l_an:
        k_angle = calculate_angle(l_hi, l_kn, l_an)
    else:
        r_hi = _get_lm(landmarks, PL.RIGHT_HIP)
        r_kn = _get_lm(landmarks, PL.RIGHT_KNEE)
        r_an = _get_lm(landmarks, PL.RIGHT_ANKLE)
        k_angle = calculate_angle(r_hi, r_kn, r_an) if (r_hi and r_kn and r_an) else None

    # ── Body rotation ─────────────────────────────────────────────────────────
    ls_xyz = _get_lm_xyz(landmarks, PL.LEFT_SHOULDER)
    rs_xyz = _get_lm_xyz(landmarks, PL.RIGHT_SHOULDER)
    lh_xyz = _get_lm_xyz(landmarks, PL.LEFT_HIP)
    rh_xyz = _get_lm_xyz(landmarks, PL.RIGHT_HIP)

    body_angle = calculate_body_rotation(ls_xyz, rs_xyz, lh_xyz, rh_xyz)
    if body_angle is not None:
        front_facing = 1 if abs(body_angle) < BODY_ROTATION_THRESHOLD_DEG else 0
    else:
        front_facing = None

    return FrameFeatures(
        shoulder_angles=s_angle,
        elbow_angles=e_angle,
        hip_angles=h_angle,
        knee_angles=k_angle,
        body_angles=body_angle,
        front_facing_boolean=front_facing,
    )


def process_frames(frames: List[np.ndarray]) -> List[FrameFeatures]:
    """
    Run MediaPipe Pose on each BGR frame and return per-frame FrameFeatures.
    Frames where pose detection fails get a FrameFeatures with all-None angles.
    """
    results: List[FrameFeatures] = []

    with mp.solutions.pose.Pose(
        static_image_mode=True,
        min_detection_confidence=MEDIAPIPE_DETECTION_CONFIDENCE,
        min_tracking_confidence=MEDIAPIPE_TRACKING_CONFIDENCE,
    ) as pose:
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pose_result = pose.process(rgb)

            if pose_result.pose_landmarks:
                features = _extract_angles(pose_result.pose_landmarks.landmark)
            else:
                features = FrameFeatures(
                    shoulder_angles=None,
                    elbow_angles=None,
                    hip_angles=None,
                    knee_angles=None,
                    body_angles=None,
                    front_facing_boolean=None,
                )
            results.append(features)

    return results
