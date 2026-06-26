import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

MODELS_DIR = PROJECT_ROOT / "models"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
STATIC_FRAMES_DIR = STATIC_DIR / "frames"

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

SCALER_PATH = MODELS_DIR / "scaler.pkl"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"

CLASS_NAMES = [
    "chest fly machine",
    "deadlift",
    "leg extension",
    "leg raises",
    "pull up",
    "squat",
    "t bar row",
]

OVR_MODEL_PATHS = {
    i: MODELS_DIR / f"xgb_ovr_{i}_{name.replace(' ', '_')}.json"
    for i, name in enumerate(CLASS_NAMES)
}

INJURY_SUPPORTED_EXERCISES = {
    "pull up",
    "squat",
    "leg extension",
    "shoulder press",
    "t bar row",
}

FRAMES_TO_SAMPLE = 50

MEDIAPIPE_DETECTION_CONFIDENCE = 0.5
MEDIAPIPE_TRACKING_CONFIDENCE = 0.5
LANDMARK_VISIBILITY_THRESHOLD = 0.5
BODY_ROTATION_THRESHOLD_DEG = 30.0

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "exercise_kb"
RAG_TOP_K = 3
CLAUDE_MODEL = "claude-sonnet-4-6"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
