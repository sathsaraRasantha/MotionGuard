# MotionGuard

**AI-powered gym exercise classification and injury risk analysis using pose estimation, machine learning, and RAG-powered coaching feedback.**

> MSc Research Project · Data Science & Artificial Intelligence · University of Sri Jayewardenepura

---

## Overview

MotionGuard analyses gym workout videos to automatically identify which exercise is being performed and flag biomechanical injury risks in key movement phases. It combines MediaPipe pose estimation, an XGBoost classifier, and a Retrieval-Augmented Generation (RAG) pipeline backed by Claude AI to produce personalised, evidence-based coaching cues.

**Core capabilities:**
- Classifies 7 gym exercises from video using majority-vote across 50 sampled frames
- Detects injury-prone phases using peer-reviewed biomechanical angle thresholds
- Generates corrective feedback grounded in academic literature via ChromaDB + Claude AI
- Serves results through a React web application with a FastAPI backend

---

## Project Structure

```
MotionGuard/
├── experiment/              # Research notebooks (feature engineering, modelling, RAG)
├── knowledge_base/          # RAG source documents per exercise (plain text)
├── models/                  # Trained XGBoost OvR models + scaler + label encoder
├── web_application/
│   ├── backend/             # FastAPI backend (pose processing, classification, RAG)
│   └── frontend/            # React + Vite + Tailwind CSS frontend
└── requirements.txt         # Root-level Python dependencies
```

---

## Experiments

All research notebooks are in `experiment/`. They follow the full pipeline from raw data to deployed models.

### 1. `keypoint_extraction.ipynb`
- Loads a public gym exercise image dataset (22 exercise categories)
- Runs MediaPipe Pose on each image and its horizontal flip
- Filters images where all exercise-relevant keypoints have visibility > 0.5
- Extracts 6 features per image: shoulder angle, elbow angle, hip angle, knee angle, body rotation, front-facing boolean
- Saves filtered images and feature CSVs; final dataset: 9 exercise classes, ~3,764 training samples

### 2. `data_preprocessing.ipynb`
- Visibility filtering and class balancing (250–550 images per class, max 550)
- Train / validation / test split generation (90 / 8 / 2)
- Handles class imbalance in OvR training via `scale_pos_weight`

### 3. `modeling.ipynb`
- Benchmarks 8 classifiers on the extracted angle features

| Model | Validation Accuracy |
|---|---|
| XGBoost (multi:softmax) | **80.0%** |
| Random Forest | 76.2% |
| K-Nearest Neighbours (k=5) | 70.8% |
| SVM (RBF) | 67.0% |
| MLP Neural Network (50 epochs) | 59.9% |
| Logistic Regression | 52.9% |

- Best model: **XGBoost OvR** (one binary classifier per class, argmax of positive-class probabilities)
- Feature importance analysis: all 5 angle features contribute roughly equally (~0.15–0.22); front-facing boolean contributes negligibly

### 4. `injury_detection.ipynb`
- Implements phase detection per exercise (e.g. dead hang → ascent → top position for pull up)
- Applies biomechanical angle thresholds sourced from peer-reviewed literature (Youdas, Escamilla, McGill et al.)
- Labels frames as `injury_prone` if steady-phase angles fall outside safe ranges
- Supported exercises: pull up, squat, leg extension, shoulder press, t bar row

### 5. `rag_feedback_notebook.ipynb`
- Indexes exercise knowledge base into ChromaDB using `all-MiniLM-L6-v2` sentence embeddings
- For each injury-prone phase, retrieves top-3 relevant passages and sends to Claude (`claude-sonnet-4-6`)
- Claude returns: severity, biomechanical summary, corrective feedback, coaching cue, literature source

---

## Web Application

### Architecture

```
Browser (React)
    │  upload video
    ▼
FastAPI  ──►  frame_extractor   (OpenCV, 50 frames)
         ──►  pose_processor    (MediaPipe Pose → 6 angle features per frame)
         ──►  classifier        (XGBoost OvR → majority vote → exercise label)
         ──►  injury_detector   (phase detection + biomechanical thresholds)
         ──►  rag_feedback      (ChromaDB retrieval + Claude API → coaching cues)
```

### Supported exercises

| Exercise | Classification | Injury Analysis |
|---|:---:|:---:|
| Pull Up | ✓ | ✓ |
| Squat | ✓ | ✓ |
| Leg Extension | ✓ | ✓ |
| T-Bar Row | ✓ | ✓ |
| Deadlift | ✓ | — |
| Chest Fly Machine | ✓ | — |
| Leg Raises | ✓ | — |

### Tech stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS 3, Axios |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| Pose estimation | MediaPipe 0.10.13, OpenCV |
| Classification | XGBoost, scikit-learn, joblib |
| RAG | ChromaDB, sentence-transformers (`all-MiniLM-L6-v2`), Anthropic Claude API |

---

## How to Run

### Prerequisites
- Python 3.11
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

---

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/MotionGuard.git
cd MotionGuard
```

---

### 2. Set up the Python environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r web_application/backend/requirements.txt
```

---

### 3. Configure environment variables

```bash
cd web_application/backend
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
BASE_URL=http://localhost:8000
```

---

### 4. Populate the ChromaDB knowledge base

On first run, the RAG pipeline needs to index the knowledge base documents. Start the backend once and the ChromaDB collection will be created automatically, or run the `rag_feedback_notebook.ipynb` notebook directly.

---

### 5. Start the backend

```bash
# From web_application/backend/
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

---

### 6. Start the frontend

```bash
cd web_application/frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

### 7. Use the app

1. Drag and drop a gym workout video (MP4, MOV, AVI, MKV, WebM)
2. Confirm the file and click **Analyse Video**
3. MotionGuard will:
   - Extract 50 frames from the video
   - Run MediaPipe pose estimation on each frame
   - Classify the exercise via majority-vote across frames
   - Detect injury-prone movement phases
   - Generate personalised coaching feedback via RAG + Claude AI
4. Results show the detected exercise, confidence score, and per-phase injury feedback with corrective cues

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a video file, returns server path |
| `POST` | `/api/classify` | Extract frames, compute pose features, classify exercise |
| `POST` | `/api/injury-detection` | Run phase-aware injury detection and generate RAG feedback |
| `GET` | `/health` | Health check |

---

## Disclaimer

MotionGuard is an academic research prototype. All feedback is generated for educational purposes only and is **not a substitute for professional medical or physiotherapy advice**.
