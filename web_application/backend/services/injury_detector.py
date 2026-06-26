"""
Phase-aware injury detection.
Ported from injury_detection.ipynb — operates on FrameFeatures objects
instead of a CSV DataFrame. No I/O, no MediaPipe dependency.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from config import BODY_ROTATION_THRESHOLD_DEG
from services.pose_processor import FrameFeatures


# ── Phase definitions ─────────────────────────────────────────────────────────
# Each exercise maps to an ordered list of phase dicts.
# The first phase whose condition is True is assigned to the frame.
# is_steady=True  → apply biomechanical thresholds
# is_steady=False → transition frame, skip thresholding

def _v(val: Optional[float]) -> float:
    return float(val) if val is not None else float("nan")


PHASE_DEFINITIONS: Dict[str, List[dict]] = {
    "pull up": [
        {
            "name": "dead_hang",
            "is_steady": True,
            "condition": lambda f: _v(f.elbow_angles) >= 155,
            "description": "Arms fully extended, hanging position",
            "thresholds": {
                "elbow_angles": {
                    "correct_range": (155, 185),
                    "injury_description": "Elbow not fully extended in dead hang — incomplete starting position",
                    "source": "Youdas et al. (2010) J. Strength Cond. Res. 24(12):3404–3414",
                },
            },
        },
        {
            "name": "top_position",
            "is_steady": True,
            "condition": lambda f: _v(f.elbow_angles) <= 75,
            "description": "Chin above bar, maximum contraction",
            "thresholds": {
                "elbow_angles": {
                    "correct_range": (40, 75),
                    "injury_description": "Elbow not sufficiently flexed at top — incomplete range of motion",
                    "source": "Youdas et al. (2010) J. Strength Cond. Res. 24(12):3404–3414",
                },
            },
        },
        {
            "name": "transition",
            "is_steady": False,
            "condition": lambda f: True,
            "description": "Mid-pull transition — not evaluated",
            "thresholds": {},
        },
    ],

    "shoulder press": [
        {
            "name": "rack_position",
            "is_steady": True,
            "condition": lambda f: _v(f.elbow_angles) <= 100 and _v(f.shoulder_angles) <= 110,
            "description": "Bar at shoulder height, start/end of press",
            "thresholds": {
                "elbow_angles": {
                    "correct_range": (75, 100),
                    "injury_description": "Elbow angle at rack indicates unsafe bar path",
                    "source": "Dillman et al. (1994) J. Sport Rehabil. 3(3):228–238",
                },
            },
        },
        {
            "name": "lockout",
            "is_steady": True,
            "condition": lambda f: _v(f.elbow_angles) >= 155,
            "description": "Arms fully extended overhead",
            "thresholds": {
                "elbow_angles": {
                    "correct_range": (155, 185),
                    "injury_description": "Elbow hyperextension at lockout — joint stress risk",
                    "source": "Kolber et al. (2014) J. Strength Cond. Res. 28(5):1213–1217",
                },
            },
        },
        {
            "name": "transition",
            "is_steady": False,
            "condition": lambda f: True,
            "description": "Mid-press transition — not evaluated",
            "thresholds": {},
        },
    ],

    "squat": [
        {
            "name": "standing",
            "is_steady": True,
            "condition": lambda f: _v(f.knee_angles) >= 155,
            "description": "Standing lockout position",
            "thresholds": {
                "hip_angles": {
                    "correct_range": (155, 185),
                    "injury_description": "Hips not fully extended at lockout — incomplete rep",
                    "source": "Schoenfeld (2010) J. Strength Cond. Res. 24(12):3497–3506",
                },
                "knee_angles": {
                    "correct_range": (155, 185),
                    "injury_description": "Knee hyperextension at lockout — posterior capsule stress",
                    "source": "Escamilla (2001) Med. Sci. Sports Exerc. 33(1):127–141",
                },
            },
        },
        {
            "name": "bottom_position",
            "is_steady": True,
            "condition": lambda f: _v(f.knee_angles) <= 100,
            "description": "Bottom of squat, maximum depth",
            "thresholds": {
                "hip_angles": {
                    "correct_range": (55, 105),
                    "injury_description": "Butt wink detected — lumbar flexion injury risk at depth",
                    "source": "Schoenfeld (2010) J. Strength Cond. Res. 24(12):3497–3506; McGill (2015)",
                },
                "knee_angles": {
                    "correct_range": (55, 100),
                    "injury_description": "Knee angle at depth outside safe range — patellar compressive stress",
                    "source": "Escamilla (2001) Med. Sci. Sports Exerc. 33(1):127–141",
                },
            },
        },
        {
            "name": "transition",
            "is_steady": False,
            "condition": lambda f: True,
            "description": "Descent / ascent transition — not evaluated",
            "thresholds": {},
        },
    ],

    "t bar row": [
        {
            "name": "start_position",
            "is_steady": True,
            "condition": lambda f: _v(f.elbow_angles) >= 150,
            "description": "Arms extended, hip hinge setup",
            "thresholds": {
                "elbow_angles": {
                    "correct_range": (150, 185),
                    "injury_description": "Elbow not fully extended at row start — incomplete ROM",
                    "source": "Fenwick et al. (2009) J. Strength Cond. Res. 23(5):1408–1417",
                },
                "hip_angles": {
                    "correct_range": (80, 145),
                    "injury_description": "Hip hinge angle outside safe range — elevated L4/L5 spinal load",
                    "source": "Fenwick et al. (2009) ibid.; McGill (2015) Back Mechanic",
                },
            },
        },
        {
            "name": "full_contraction",
            "is_steady": True,
            "condition": lambda f: _v(f.elbow_angles) <= 80,
            "description": "Bar at chest, maximum contraction",
            "thresholds": {
                "elbow_angles": {
                    "correct_range": (50, 80),
                    "injury_description": "Elbow over-flexed at contraction — bicep tendon stress",
                    "source": "Fenwick et al. (2009) J. Strength Cond. Res. 23(5):1408–1417",
                },
                "hip_angles": {
                    "correct_range": (80, 145),
                    "injury_description": "Hip angle collapsed during row — lumbar stress risk",
                    "source": "Fenwick et al. (2009) ibid.; McGill (2015) Back Mechanic",
                },
            },
        },
        {
            "name": "transition",
            "is_steady": False,
            "condition": lambda f: True,
            "description": "Mid-row transition — not evaluated",
            "thresholds": {},
        },
    ],

    "leg extension": [
        {
            "name": "start_bent",
            "is_steady": True,
            "condition": lambda f: _v(f.knee_angles) < 110,
            "description": "Starting position, knee flexed",
            "thresholds": {
                "knee_angles": {
                    "correct_range": (70, 109),
                    "injury_description": "Knee over-flexed at start — patellofemoral compressive force risk",
                    "source": "Steinkamp et al. (1993) Am. J. Sports Med. 21(3):438–444",
                },
            },
        },
        {
            "name": "extended",
            "is_steady": True,
            "condition": lambda f: True,
            "description": "Leg extended position",
            "thresholds": {
                "knee_angles": {
                    "correct_range": (110, 175),
                    "injury_description": "Knee hyperextension on leg extension — posterior capsule and ACL stress",
                    "source": "Witvrouw et al. (2004) Am. J. Sports Med. 32(5):1122–1130",
                },
            },
        },
    ],
}

ANGLE_COLUMNS = ["elbow_angles", "hip_angles", "knee_angles"]


@dataclass
class LabeledFrame:
    frame_index: int
    phase: str
    is_steady: bool
    label: str                          # correct / injury_prone / transition / rotated_view
    violated_rules: str = ""
    violated_sources: str = ""
    flag_elbow: str = "not_applicable"
    flag_hip: str = "not_applicable"
    flag_knee: str = "not_applicable"
    elbow_angles: Optional[float] = None
    hip_angles: Optional[float] = None
    knee_angles: Optional[float] = None


def _is_rotated(ff: FrameFeatures) -> bool:
    if ff.body_angles is not None:
        return abs(ff.body_angles) > BODY_ROTATION_THRESHOLD_DEG
    if ff.front_facing_boolean is not None:
        return ff.front_facing_boolean == 0
    return False


def _detect_phase(ff: FrameFeatures, exercise: str) -> Tuple[str, bool, str, dict]:
    for phase in PHASE_DEFINITIONS.get(exercise, []):
        try:
            if phase["condition"](ff):
                return phase["name"], phase["is_steady"], phase["description"], phase["thresholds"]
        except Exception:
            continue
    return "unknown", False, "Phase not determined", {}


def _apply_thresholds(ff: FrameFeatures, thresholds: dict) -> Tuple[str, str, str, dict]:
    violated, sources, flags = [], [], {}
    values = {
        "elbow_angles": ff.elbow_angles,
        "hip_angles": ff.hip_angles,
        "knee_angles": ff.knee_angles,
    }
    for col in ANGLE_COLUMNS:
        rule = thresholds.get(col)
        if rule is None:
            flags[col] = "not_applicable"
            continue
        val = values[col]
        if val is None or np.isnan(val):
            flags[col] = "missing"
            continue
        lo, hi = rule["correct_range"]
        if val < lo or val > hi:
            violated.append(f"{col}={val:.1f}° outside [{lo}°–{hi}°]: {rule['injury_description']}")
            sources.append(rule["source"])
            flags[col] = "injury_prone"
        else:
            flags[col] = "correct"

    label = "injury_prone" if violated else "correct"
    return label, " | ".join(violated), " | ".join(set(sources)), flags


def label_frames(
    frame_features: List[FrameFeatures], exercise: str
) -> List[LabeledFrame]:
    """
    Apply phase detection and injury thresholds to each FrameFeatures.
    Returns one LabeledFrame per input frame.
    """
    labeled: List[LabeledFrame] = []

    for idx, ff in enumerate(frame_features):
        if not ff.is_valid():
            labeled.append(LabeledFrame(
                frame_index=idx, phase="unknown", is_steady=False, label="no_pose"
            ))
            continue

        phase_name, is_steady, _, thresholds = _detect_phase(ff, exercise)

        if not is_steady:
            labeled.append(LabeledFrame(
                frame_index=idx, phase=phase_name, is_steady=False, label="transition",
                elbow_angles=ff.elbow_angles, hip_angles=ff.hip_angles, knee_angles=ff.knee_angles,
            ))
            continue

        if _is_rotated(ff):
            labeled.append(LabeledFrame(
                frame_index=idx, phase=phase_name, is_steady=True, label="rotated_view",
                elbow_angles=ff.elbow_angles, hip_angles=ff.hip_angles, knee_angles=ff.knee_angles,
            ))
            continue

        label, violated_rules, violated_sources, flags = _apply_thresholds(ff, thresholds)
        labeled.append(LabeledFrame(
            frame_index=idx,
            phase=phase_name,
            is_steady=True,
            label=label,
            violated_rules=violated_rules,
            violated_sources=violated_sources,
            flag_elbow=flags.get("elbow_angles", "not_applicable"),
            flag_hip=flags.get("hip_angles", "not_applicable"),
            flag_knee=flags.get("knee_angles", "not_applicable"),
            elbow_angles=ff.elbow_angles,
            hip_angles=ff.hip_angles,
            knee_angles=ff.knee_angles,
        ))

    return labeled
