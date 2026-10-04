import json
from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import render

from .forms import TransactionForm
from .services import get_predictor, reports_dir


# ============================================================
# Helpers
# ============================================================

def _load_json(path, default=None):
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return default if default is not None else {}


def _metrics():
    return _load_json(reports_dir() / "evaluation_metrics.json", {})


# ============================================================
# Pages
# ============================================================

def overview(request):
    m = _metrics()
    test = m.get("test", {})
    val = m.get("validation", {})

    context = {
        "active": "overview",
        "model_name": m.get("model_name", "XGBoost"),
        "threshold": m.get("threshold"),
        "features_used": m.get("features_used"),
        "metrics": {
            "pr_auc": test.get("pr_auc"),
            "roc_auc": test.get("roc_auc"),
            "precision": test.get("precision"),
            "recall": test.get("recall"),
            "f1": test.get("f1"),
            "val_pr_auc": val.get("pr_auc"),
        },
    }
    return render(request, "fraud_portal/overview.html", context)


def assessment(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            payload = form.to_payload()
            result = get_predictor().predict_one(payload)
            return render(
                request,
                "fraud_portal/result.html",
                {
                    "active": "assessment",
                    "payload": payload,
                    "result": result,
                },
            )
    else:
        form = TransactionForm()

    return render(
        request,
        "fraud_portal/assessment.html",
        {"active": "assessment", "form": form},
    )


def model_performance(request):
    m = _metrics()
    context = {
        "active": "model",
        "model_name": m.get("model_name", "XGBoost"),
        "threshold": m.get("threshold"),
        "features_used": m.get("features_used"),
        "validation": m.get("validation", {}),
        "test": m.get("test", {}),
        "best_f1_threshold": m.get("best_f1_threshold_on_test"),
        "best_f1": m.get("best_f1_on_test"),
        "segments": m.get("segment_recall_test", []),
        "plots": [
            ("pr_curve.png",
             "Precision–Recall curve",
             "On this imbalanced dataset, PR-AUC is the metric that matters. "
             "A random classifier would sit at ~1.7%."),
            ("roc_curve.png",
             "ROC curve",
             "For reference and comparison with published baselines."),
            ("threshold_analysis.png",
             "Precision / Recall / F1 vs threshold",
             "Where to set the operational decision boundary."),
            ("confusion_matrix.png",
             "Confusion matrix",
             "At the model's operational threshold."),
            ("score_distribution.png",
             "Score distribution",
             "How well the model separates fraud from legitimate activity."),
            ("feature_importance.png",
             "Feature importance (XGBoost gain)",
             "The signal the model leans on most."),
            ("recall_by_segment.png",
             "Recall by segment",
             "Which fraud patterns the model catches best."),
            ("shap_summary.png",
             "SHAP summary (beeswarm)",
             "Global feature effect on fraud probability."),
            ("shap_bar.png",
             "Mean |SHAP|",
             "Magnitude-only view of feature influence."),
        ],
    }
    return render(request, "fraud_portal/model.html", context)


def methodology(request):
    return render(
        request,
        "fraud_portal/methodology.html",
        {"active": "methodology"},
    )


# ============================================================
# Plot serving — reads PNGs straight from the reports dir
# ============================================================

ALLOWED_PLOTS = {
    "pr_curve.png", "roc_curve.png", "threshold_analysis.png",
    "confusion_matrix.png", "score_distribution.png",
    "feature_importance.png", "recall_by_segment.png",
    "shap_summary.png", "shap_bar.png",
    "shap_waterfall_fraud.png", "shap_waterfall_legit.png",
    "shap_waterfall_false_negative.png",
}


def plot(request, filename):
    if filename not in ALLOWED_PLOTS:
        raise Http404
    path = Path(reports_dir()) / filename
    if not path.exists():
        raise Http404
    return FileResponse(open(path, "rb"), content_type="image/png")