"""
RAG pipeline: ChromaDB retrieval + Claude API feedback generation.
Ported from rag_feedback_notebook.ipynb. Loaded once at startup.
"""
import json
import re
from collections import defaultdict
from typing import Dict, List, Optional

import anthropic
import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    ANTHROPIC_API_KEY,
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_DIR,
    CLAUDE_MODEL,
    EMBEDDING_MODEL,
    RAG_TOP_K,
)
from services.injury_detector import LabeledFrame


class RAGFeedbackService:
    """Loaded once at startup via FastAPI lifespan; shared across all requests."""

    def __init__(self):
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        self.collection = self.chroma_client.get_collection(CHROMA_COLLECTION_NAME)
        self.claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def _build_query(
        self,
        exercise: str,
        phase: str,
        violated_rules: str,
        angles: Dict[str, Optional[float]],
    ) -> str:
        angle_str = ", ".join(
            f"{k}={v:.1f}°" for k, v in angles.items() if v is not None
        )
        return (
            f"Exercise: {exercise}\n"
            f"Phase: {phase}\n"
            f"Detected violations: {violated_rules}\n"
            f"Angle values: {angle_str}\n"
            "What is the biomechanical risk and how should the athlete correct their form?"
        )

    def _retrieve(self, query: str, exercise: str, phase: str) -> List[dict]:
        embedding = self.embed_model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=min(RAG_TOP_K, self.collection.count()),
            where={"$and": [{"exercise": {"$eq": exercise}}, {"phase": {"$eq": phase}}]},
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                chunks.append({"text": doc, "metadata": meta, "similarity": round(1 - dist, 3)})
        return chunks

    # ── Generation ────────────────────────────────────────────────────────────

    def _generate(
        self,
        exercise: str,
        phase: str,
        violated_rules: str,
        angles: Dict[str, Optional[float]],
        chunks: List[dict],
    ) -> dict:
        context = "\n\n---\n\n".join(
            f"[Reference {i} | similarity: {c['similarity']}]\n{c['text']}"
            for i, c in enumerate(chunks, 1)
        )
        angle_str = ", ".join(
            f"{k}: {v:.1f}°" for k, v in angles.items() if v is not None
        )
        severities = [c["metadata"].get("severity", "warning") for c in chunks]
        severity = "danger" if "danger" in severities else "warning"

        prompt = f"""You are an expert exercise physiotherapist and strength coach.
A pose estimation system has detected an injury-prone exercise position.

DETECTED SITUATION:
- Exercise: {exercise}
- Phase: {phase}
- Violations: {violated_rules}
- Measured angles: {angle_str}

BIOMECHANICAL REFERENCE MATERIAL:
{context}

Based ONLY on the reference material above, provide corrective feedback.
Respond in JSON with exactly these fields:
{{
  "severity": "{severity}",
  "summary": "One sentence describing the main problem detected",
  "feedback": "2-3 sentences of specific corrective feedback referencing the actual angle values",
  "cue": "One short coaching cue the athlete can remember (under 10 words)",
  "source": "The citation(s) from the reference material that support this feedback"
}}

Rules:
- Always reference the specific angle values in the feedback
- Do not invent information not in the reference material
- Keep the cue under 10 words
- Be direct and actionable, not generic
Respond with valid JSON only."""

        response = self.claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {
                "severity": severity,
                "summary": f"Injury-prone position detected in {exercise} at {phase}",
                "feedback": raw[:300],
                "cue": "Check your form",
                "source": chunks[0]["metadata"].get("source", "") if chunks else "",
            }

    # ── Public interface ──────────────────────────────────────────────────────

    def generate_feedback_for_violations(
        self, exercise: str, injury_frames: List[LabeledFrame]
    ) -> List[dict]:
        """
        Groups injury_prone frames by phase, makes one Claude call per unique
        phase (using the most representative frame per group), and returns a
        list of feedback dicts — one entry per phase that had violations.
        """
        by_phase: Dict[str, List[LabeledFrame]] = defaultdict(list)
        for lf in injury_frames:
            by_phase[lf.phase].append(lf)

        results = []
        for phase, frames in by_phase.items():
            # Use the first frame as the representative for this phase
            rep = frames[0]
            angles = {
                "elbow": rep.elbow_angles,
                "hip": rep.hip_angles,
                "knee": rep.knee_angles,
            }
            query = self._build_query(exercise, phase, rep.violated_rules, angles)
            chunks = self._retrieve(query, exercise, phase)

            if not chunks:
                results.append({
                    "phase": phase,
                    "injury_prone_frame_count": len(frames),
                    "violated_rules": rep.violated_rules,
                    "severity": "warning",
                    "summary": f"Injury-prone position detected in {exercise} at {phase}",
                    "feedback": f"Violation: {rep.violated_rules}. Please review your form.",
                    "cue": "Check your form",
                    "source": "",
                })
                continue

            feedback = self._generate(exercise, phase, rep.violated_rules, angles, chunks)
            results.append({
                "phase": phase,
                "injury_prone_frame_count": len(frames),
                "violated_rules": rep.violated_rules,
                **feedback,
            })

        return results
