"""
services.py
Django-facing wrapper around the ML predictor.

The heavy `predictor.py` module lives under ml/fraud_detection/src/
and has no Django imports. This file:
  * puts the ML src directory on sys.path once
  * caches the FraudPredictor so the model loads exactly once per worker
"""

import sys
from functools import lru_cache
from pathlib import Path

from django.conf import settings

# ---- Paths -----------------------------------------------------------
PROJECT_ROOT = Path(settings.BASE_DIR)
ML_SRC = PROJECT_ROOT / "ml" / "fraud_detection" / "src"
ML_MODEL = PROJECT_ROOT / "ml" / "fraud_detection" / "models" / "fraud_model.pkl"
ML_REPORTS = PROJECT_ROOT / "ml" / "fraud_detection" / "reports"

# Make predictor importable from anywhere in Django
if str(ML_SRC) not in sys.path:
    sys.path.insert(0, str(ML_SRC))


@lru_cache(maxsize=1)
def get_predictor():
    """
    Return the singleton FraudPredictor. Loaded lazily on first call
    and cached for the lifetime of the worker process.
    """
    from predictor import FraudPredictor  # noqa: E402

    return FraudPredictor(ML_MODEL, build_shap=True)


def reports_dir() -> Path:
    return ML_REPORTS