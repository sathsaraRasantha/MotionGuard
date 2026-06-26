"""
Three API endpoints sharing one internal pipeline.
- POST /api/upload            save video to disk, return server path
- POST /api/classify          extract frames + angles, majority-vote exercise
- POST /api/injury-detection  same frames + angles, phase-aware injury labels + RAG feedback
"""
import shutil
import uuid
from collections import defaultdict

import cv2
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from config import BASE_URL, STATIC_FRAMES_DIR, UPLOADS_DIR
from schemas.classification import ClassifyRequest, ClassifyResponse
from schemas.injury import InjuryRequest, InjuryResponse, PhaseFeedback
from services.frame_extractor import extract_frames
from services.injury_detector import label_frames
from services.pose_processor import process_frames

router = APIRouter(prefix="/api", tags=["analysis"])

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
    "video/webm",
}


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _run_shared_pipeline(video_path: str):
    """
    Extract 50 frames and compute angles once.
    Returns (frames, frame_features). Raises HTTPException on file errors.
    """
    try:
        frames = extract_frames(video_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not frames:
        raise HTTPException(status_code=422, detail="No frames could be extracted from the video.")

    frame_features = process_frames(frames)
    return frames, frame_features


def _save_injury_frames(frames, injury_frames_by_phase: dict, session_id: str) -> dict:
    """
    For each injury-prone phase, save the representative frame as a JPEG.
    Returns {phase_name: absolute_url}.
    """
    session_dir = STATIC_FRAMES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    phase_urls = {}
    for phase, phase_frames in injury_frames_by_phase.items():
        rep = phase_frames[0]
        if rep.frame_index < len(frames):
            filename = f"{phase.replace(' ', '_')}.jpg"
            cv2.imwrite(str(session_dir / filename), frames[rep.frame_index])
            phase_urls[phase] = f"{BASE_URL}/static/frames/{session_id}/{filename}"

    return phase_urls


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Accept a video file upload, save to the uploads directory, and return
    the server-side path for use with /classify and /injury-detection.
    """
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Accepted: mp4, mov, avi, mkv, webm.",
        )

    filename = f"{uuid.uuid4()}_{file.filename}"
    save_path = UPLOADS_DIR / filename

    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"video_path": str(save_path), "filename": file.filename}


@router.post("/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest, app_request: Request):
    """
    Extract 50 evenly-spaced frames, compute joint angles, and classify
    the exercise via OvR XGBoost majority voting.
    """
    classifier = app_request.app.state.classifier
    _, frame_features = _run_shared_pipeline(request.video_path)

    valid_count = sum(1 for ff in frame_features if ff.is_valid())
    exercise, confidence, votes = classifier.classify(frame_features)

    return ClassifyResponse(
        exercise=exercise,
        confidence=confidence,
        total_frames=len(frame_features),
        valid_frames=valid_count,
        votes=votes,
    )


@router.post("/injury-detection", response_model=InjuryResponse)
def injury_detection(request: InjuryRequest, app_request: Request):
    """
    Extract 50 evenly-spaced frames, compute angles once, run phase-aware
    injury detection, save injury-prone frame images, and generate
    RAG-backed corrective feedback per unique violated phase.
    """
    exercise = request.exercise.strip().lower()

    from config import INJURY_SUPPORTED_EXERCISES
    if exercise not in INJURY_SUPPORTED_EXERCISES:
        return InjuryResponse(
            exercise=exercise,
            supported=False,
            total_frames=0,
            valid_frames=0,
            steady_phase_frames=0,
            injury_prone_frames=0,
            overall_severity=None,
            feedback=[],
        )

    rag = app_request.app.state.rag
    frames, frame_features = _run_shared_pipeline(request.video_path)

    labeled = label_frames(frame_features, exercise)

    valid_count = sum(1 for lf in labeled if lf.label != "no_pose")
    steady_count = sum(1 for lf in labeled if lf.is_steady)
    injury_labeled = [lf for lf in labeled if lf.label == "injury_prone"]

    overall_severity = None
    feedback_list = []

    if injury_labeled:
        # Group by phase for frame saving and deduplication of RAG calls
        by_phase = defaultdict(list)
        for lf in injury_labeled:
            by_phase[lf.phase].append(lf)

        session_id = str(uuid.uuid4())
        phase_image_urls = _save_injury_frames(frames, by_phase, session_id)

        raw_feedback = rag.generate_feedback_for_violations(exercise, injury_labeled)

        for fb in raw_feedback:
            phase = fb.get("phase", "")
            feedback_list.append(
                PhaseFeedback(**fb, frame_image_url=phase_image_urls.get(phase))
            )

        severities = [fb.severity for fb in feedback_list]
        overall_severity = "danger" if "danger" in severities else "warning"

    return InjuryResponse(
        exercise=exercise,
        supported=True,
        total_frames=len(frame_features),
        valid_frames=valid_count,
        steady_phase_frames=steady_count,
        injury_prone_frames=len(injury_labeled),
        overall_severity=overall_severity,
        feedback=feedback_list,
    )
