from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import STATIC_DIR, STATIC_FRAMES_DIR, UPLOADS_DIR
from routers.analysis import router as analysis_router
from services.classifier import ExerciseClassifier
from services.rag_feedback import RAGFeedbackService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure runtime directories exist
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    # Load heavy models once at startup — shared across all requests
    print("Loading exercise classifier...")
    app.state.classifier = ExerciseClassifier()
    print("Loading RAG feedback service...")
    app.state.rag = RAGFeedbackService()
    print("All models loaded. Server ready.")
    yield


app = FastAPI(
    title="MotionGuard API",
    description="Exercise classification and injury detection from local video files.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(analysis_router)


@app.get("/health")
def health():
    return {"status": "ok"}
