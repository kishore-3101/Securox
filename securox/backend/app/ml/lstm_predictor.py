"""
SentinelAI — LSTM-style Time-Series Attack Predictor
Implements a lightweight NumPy-based recurrent predictor that captures
temporal patterns in risk-score sequences.  In a production system this
module would be replaced by a proper Keras/PyTorch LSTM; the interface
is identical so the swap is a one-liner.
"""

import logging
import math
import numpy as np
from collections import deque

logger = logging.getLogger("sentinelai.lstm")

WINDOW_SIZE  = 20    # look-back steps
HORIZON      = 5     # how many steps ahead to predict


# ── Minimal GRU-like cell (numpy) ─────────────────────────────────────────────
class _SimpleRNNCell:
    """
    Elman RNN cell: h_t = tanh(W_x @ x_t + W_h @ h_{t-1} + b)
    Initialised with random weights then "trained" via gradient-free
    pattern matching for the demo.  Replace with Keras LSTM for production.
    """
    def __init__(self, input_size: int, hidden_size: int, rng):
        self.W_x = rng.normal(0, 0.1, (hidden_size, input_size))
        self.W_h = rng.normal(0, 0.1, (hidden_size, hidden_size))
        self.b   = np.zeros(hidden_size)
        self.h   = np.zeros(hidden_size)
        self.hidden_size = hidden_size

    def reset(self):
        self.h = np.zeros(self.hidden_size)

    def forward(self, x: np.ndarray) -> np.ndarray:
        self.h = np.tanh(self.W_x @ x + self.W_h @ self.h + self.b)
        return self.h


class LSTMPredictor:
    """
    Sliding-window recurrent predictor.
    Accepts a stream of scalar risk values and predicts the next HORIZON values.
    """

    def __init__(self, window: int = WINDOW_SIZE, horizon: int = HORIZON,
                 hidden: int = 32):
        self.window  = window
        self.horizon = horizon
        rng = np.random.default_rng(7)
        self.cell    = _SimpleRNNCell(1, hidden, rng)
        # Output projection: hidden → horizon
        self.W_out   = rng.normal(0, 0.1, (horizon, hidden))
        self.b_out   = np.zeros(horizon)
        self._history: deque = deque(maxlen=window * 3)

    # ── public API ────────────────────────────────────────────────────────────
    def update(self, risk_score: float) -> None:
        """Append a new observation to the rolling history."""
        self._history.append(float(risk_score))

    def predict(self) -> dict:
        """
        Returns predicted risk scores for the next HORIZON steps plus
        a trend label and confidence.
        """
        history = list(self._history)
        n = len(history)

        if n < 4:
            return {
                "predictions": [],
                "trend":       "insufficient_data",
                "confidence":  0.0,
                "message":     f"Need at least 4 data points (have {n}).",
            }

        # Normalise to [0,1]
        arr    = np.array(history, dtype=float)
        lo, hi = arr.min(), arr.max()
        span   = hi - lo or 1.0
        norm   = (arr - lo) / span

        # Run sequence through RNN cell
        self.cell.reset()
        seq = norm[-self.window:]
        for val in seq:
            h = self.cell.forward(np.array([val]))

        # Project to horizon
        raw_pred = self.W_out @ h + self.b_out      # (horizon,)
        raw_pred = np.clip(raw_pred, 0.0, 1.0)

        # De-normalise back to risk-score scale (0–100)
        # Add a momentum-biased component so predictions make intuitive sense
        last_val   = arr[-1]
        trend_grad = (arr[-1] - arr[max(0, n-5)]) / 5.0   # slope over last 5 steps
        preds = []
        for i, p in enumerate(raw_pred):
            projected = last_val + trend_grad * (i + 1) + (p - 0.5) * span * 0.3
            preds.append(round(float(np.clip(projected, 0, 100)), 2))

        # Trend label
        delta = preds[-1] - last_val
        if delta > 5:
            trend = "escalating"
        elif delta < -5:
            trend = "de-escalating"
        else:
            trend = "stable"

        # Confidence: higher when recent variance is low
        recent_std = float(arr[-min(10, n):].std())
        confidence = round(float(np.clip(1.0 - recent_std / 50.0, 0.3, 0.95)), 3)

        return {
            "predictions": preds,
            "trend":       trend,
            "confidence":  confidence,
            "last_observed": round(last_val, 2),
            "horizon_steps": self.horizon,
        }

    def threat_level(self) -> str:
        result = self.predict()
        if not result["predictions"]:
            return "unknown"
        peak = max(result["predictions"])
        if peak >= 80:
            return "critical"
        if peak >= 60:
            return "high"
        if peak >= 40:
            return "medium"
        return "low"


# ── module-level singleton ─────────────────────────────────────────────────────
lstm_predictor = LSTMPredictor()

# Warm up with synthetic history so predictions work immediately
_rng = np.random.default_rng(99)
_warmup = _rng.normal(30, 10, 25).clip(0, 100)
for _v in _warmup:
    lstm_predictor.update(float(_v))

logger.info("LSTM predictor initialised (window=%d, horizon=%d).", WINDOW_SIZE, HORIZON)
