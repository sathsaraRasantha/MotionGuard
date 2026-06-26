"""
Loads the saved OvR XGBoost classifiers, scaler, and label encoder,
then classifies exercise type from a list of FrameFeatures via majority voting.
"""
import joblib
import numpy as np
from collections import Counter
from typing import Dict, List, Tuple

from xgboost import XGBClassifier

from config import CLASS_NAMES, LABEL_ENCODER_PATH, OVR_MODEL_PATHS, SCALER_PATH
from services.pose_processor import FrameFeatures


class ExerciseClassifier:
    """Loaded once at startup via FastAPI lifespan; shared across all requests."""

    def __init__(self):
        self.scaler = joblib.load(SCALER_PATH)
        self.label_encoder = joblib.load(LABEL_ENCODER_PATH)
        self.models: Dict[int, XGBClassifier] = {}
        for cls_idx, path in OVR_MODEL_PATHS.items():
            m = XGBClassifier()
            m.load_model(str(path))
            self.models[cls_idx] = m

    def _predict_frame(self, feature_row: List[float]) -> str:
        """
        Run all 7 OvR binary classifiers on one feature row.
        Returns the class label with the highest positive-class probability.
        """
        X = np.array(feature_row).reshape(1, -1)
        X[:, :-1] = self.scaler.transform(X[:, :-1])   # scale all except front_facing bool
        probs = np.array([
            self.models[i].predict_proba(X)[0, 1]
            for i in range(len(self.models))
        ])
        return self.label_encoder.inverse_transform([np.argmax(probs)])[0]

    def classify(
        self, frame_features: List[FrameFeatures]
    ) -> Tuple[str, float, Dict[str, int]]:
        """
        Majority-vote across all valid frames to determine exercise type.

        Returns:
            (predicted_exercise, confidence, votes_per_class)
            confidence = winning_votes / total_valid_frames
        """
        votes: List[str] = []
        for ff in frame_features:
            row = ff.to_feature_row()
            if row is None:
                continue
            label = self._predict_frame(row)
            votes.append(label)

        if not votes:
            return "unknown", 0.0, {}

        EXCLUDED = {"chest fly machine"}
        excluded_count = sum(1 for v in votes if v in EXCLUDED)
        filtered_votes  = [v for v in votes if v not in EXCLUDED]

        if not filtered_votes:
            return "unknown", 0.0, {}

        vote_counts = Counter(filtered_votes)
        winner = vote_counts.most_common(1)[0][0]

        # Redistribute excluded votes onto the winner
        vote_counts[winner] += excluded_count

        confidence = vote_counts[winner] / len(votes)
        return winner, round(confidence, 4), dict(vote_counts)
