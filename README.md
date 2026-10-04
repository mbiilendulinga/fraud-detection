# Fraud Detection

A Django application that estimates the probability a banking transaction
is fraudulent. Built end to end: synthetic data generation, temporal feature
engineering, model training, explainability with SHAP, and a live web
interface.

Enter a transaction and customer profile, and the app returns a fraud
probability, a risk band, a decision recommendation, the SHAP contributors
that drove the prediction, and a full model-performance dashboard.

---

Portfolio : https://www.mbiile.com/fraud-portal/

## Quick start

Get the app running in about 5 minutes.

### 1. Clone and enter the project

```bash
git clone https://github.com/mbiilendulinga/fraud-detection.git
cd fraud-detection
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

This creates the SQLite database tables. You don't need any data in them —
the prediction service reads from the committed model file and reports
directory.

### 5. Start the server

```bash
python manage.py runserver
```

### 6. Open the app

```
http://127.0.0.1:8000/
```

Try:
- **Overview** — landing page with headline metrics
- **Score a transaction** — fill in a transaction and submit
- **Model performance** — PR/ROC curves, confusion matrix, SHAP plots
- **Methodology** — how the data and model were built

That's it. The trained model and evaluation reports are committed, so no
data generation or training is required for a local demo.

---

## Need the raw data?

The raw database — 5,000 clients, 100,000 transactions, and 100,000
metadata rows — is **not committed** to the repo. It's regenerated from
scratch using a seeded script, which is faster than cloning a MySQL dump
and produces the exact same dataset every time.

If you want to rebuild everything end to end, run these five scripts in
order:

```bash
python ml/fraud_detection/src/generate_data.py      # builds the DB (~15 s)
python ml/fraud_detection/src/validate_data.py      # 11 integrity checks
python ml/fraud_detection/src/build_features.py     # produces Parquet splits
python ml/fraud_detection/src/train.py              # trains LR + XGBoost
python ml/fraud_detection/src/evaluate.py           # writes plots & reports
```

The generation step takes about 15 seconds because the fraud patterns are
constructed analytically rather than simulated minute-by-minute. Total
end-to-end time is under two minutes on a laptop.

After running these you have:

- A fully populated SQLite database
- `train.parquet`, `validation.parquet`, `test.parquet` in
  `ml/fraud_detection/data/processed/`
- `fraud_model.pkl` and `feature_importance.csv` in
  `ml/fraud_detection/models/`
- Evaluation plots and `evaluation_metrics.json` in
  `ml/fraud_detection/reports/`

This is also how the committed model and reports were originally produced.

---

## Configuration

By default the app uses SQLite — nothing to configure. If you want to
override settings, create a `.env` file at the project root:

```
DJANGO_SECRET_KEY=replace-me-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Then reload the server.

---

## Rebuilding from scratch

Full reproduction, start to finish.

### 1. Generate the synthetic dataset

```bash
python ml/fraud_detection/src/generate_data.py
```

Creates 5,000 clients, then 100,000 transactions and matching metadata
rows, with fraud injected at 1.7% using five distinct patterns. Writes
directly to SQLite via bulk-create batches.

Takes about 15 seconds.

### 2. Validate the dataset

```bash
python ml/fraud_detection/src/validate_data.py
```

Runs 11 integrity and signal checks: row counts, foreign keys, balance
continuity, fraud rate, hour-of-day distribution, timestamp spread,
amount separation between fraud and legitimate, velocity bursts, device
novelty, geographic anomaly, and international signal.

Expected result: `All checks passed. Dataset looks healthy.`

### 3. Build the feature dataset

```bash
python ml/fraud_detection/src/build_features.py
```

Loads the three database tables, joins them, sorts per client, and applies
nine families of temporal feature engineering. Splits the result
chronologically into 70/15/15 train/validation/test and writes three
Parquet files plus a `feature_columns.json`.

Produces 82 model-ready features across ~150 seconds.

### 4. Train and compare two models

```bash
python ml/fraud_detection/src/train.py
```

Trains Logistic Regression (baseline) and XGBoost on the same feature set
with class weighting. Prints a comparison table, saves the better model
as `fraud_model.pkl`, and writes the top-15 feature importance list.

Takes about 45 seconds.

### 5. Evaluate and generate figures

```bash
python ml/fraud_detection/src/evaluate.py
```

Produces precision-recall curve, ROC curve, threshold analysis, confusion
matrix, score distribution, feature importance, per-segment recall, and
four SHAP visualisations (beeswarm, bar, and waterfall plots for a true
positive, a true negative, and a missed fraud).

Takes about 30 seconds including SHAP.

Then restart the Django server and reload the Model Performance page.

---

## Model

Two classifiers trained on the same 82-feature dataset with the same
chronological split.

| Model | PR-AUC | ROC-AUC | Recall @ P ≥ 0.5 |
|---|---|---|---|
| Logistic Regression | 0.9841 | 0.9994 | 0.9894 |
| **XGBoost ★** | **0.9977** | **1.0000** | **1.0000** |

XGBoost was selected as the production model. It won on PR-AUC — the
metric that actually matters for 1.7% positive-class data — and it
handles the class imbalance and nonlinear interactions natively via
`scale_pos_weight`, without any manual resampling.

The operational threshold was chosen by maximising F1 on the validation
set: **0.7032**. Every prediction on the website uses this threshold.

---

## Dataset

Fully synthetic. Generated transaction by transaction so that balance
chains, device histories, and merchant relationships hold throughout
each client's four-year timeline.

| Table | Rows |
|---|---|
| `clients` | 5,000 |
| `transactions` | 100,000 |
| `transaction_metadata` | 100,000 |
| Fraudulent transactions | 1,700 (1.70%) |

Fraud is not randomly labelled. Five distinct patterns are injected, each
with its own behavioural footprint:

- **Account takeover** — new device, foreign country, overnight hour, large amount
- **Card compromise** — new device, POS or online channel, mismatched payment method
- **Velocity attack** — 3–5 consecutive transactions within minutes
- **Geographic anomaly** — transaction far from the client's home province
- **Merchant anomaly** — high-risk merchant category the client has never used

The feature engineering step expands this into 82 predictors grouped into
nine families (temporal, balance, behavioural, sequence, velocity,
location, device, merchant, interaction).

---

## Project structure

```
fraud-detection/
├── manage.py
├── requirements.txt
├── LICENSE
├── README.md
│
├── mysite/                            Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── fraud_portal/                      Django app
│   ├── models.py                      Client, Transaction, TransactionMetadata
│   ├── forms.py                       Transaction scoring form
│   ├── views.py                       Page handlers + plot server
│   ├── urls.py
│   ├── services.py                    Loads FraudPredictor singleton
│   ├── migrations/
│   ├── templates/fraud_portal/
│   │   ├── base.html
│   │   ├── overview.html
│   │   ├── assessment.html
│   │   ├── result.html
│   │   ├── model.html
│   │   └── methodology.html
│   └── static/
│       ├── css/fraud_detection.css
│       └── js/fraud_detection.js
│
└── ml/fraud_detection/
    ├── data/processed/
    │   ├── train.parquet
    │   ├── validation.parquet
    │   ├── test.parquet
    │   └── feature_columns.json
    ├── models/
    │   ├── fraud_model.pkl                 ← primary model + threshold
    │   └── feature_importance.csv
    ├── reports/
    │   ├── evaluation_metrics.json
    │   ├── evaluation_summary.txt
    │   ├── pr_curve.png
    │   ├── roc_curve.png
    │   ├── threshold_analysis.png
    │   ├── confusion_matrix.png
    │   ├── score_distribution.png
    │   ├── feature_importance.png
    │   ├── recall_by_segment.png
    │   ├── shap_summary.png
    │   ├── shap_bar.png
    │   ├── shap_waterfall_fraud.png
    │   ├── shap_waterfall_legit.png
    │   └── shap_waterfall_false_negative.png
    └── src/
        ├── generate_data.py
        ├── validate_data.py
        ├── build_features.py
        ├── train.py
        ├── evaluate.py
        ├── predictor.py               ← reusable scoring class
        └── cli.py                     ← command-line interface
```

---

## Using the predictor outside Django

The `FraudPredictor` class in `ml/fraud_detection/src/predictor.py` has no
Django imports — you can score transactions from a notebook, a CLI, or
any Python script.

**Command line:**

```bash
python ml/fraud_detection/src/cli.py --example
python ml/fraud_detection/src/cli.py --example-legit
python ml/fraud_detection/src/cli.py --payload my_transaction.json
python ml/fraud_detection/src/cli.py --interactive
```

python:

```python
from predictor import FraudPredictor

predictor = FraudPredictor("ml/fraud_detection/models/fraud_model.pkl")
result = predictor.predict_one({
    "amount": 45000,
    "transaction_type": "Transfer",
    "channel": "Online Banking",
    "transaction_hour": 3,
    "is_international": 1,
    "is_new_device": 1,
    "transactions_last_1h": 4,
    "monthly_income": 45000,
    # ...any other fields
})

print(result["probability"])   # 0.9987
print(result["risk_band"])     # CRITICAL
for f in result["top_features"]:
    print(f["feature"], f["shap"], f["direction"])
```

The class caches the loaded model and is safe to reuse — Django wraps it
in an `lru_cache` so the pickle is read once per worker, not per request.

---

## Tech stack

- Python 3.11+
- Django 5.x
- SQLite (default)
- pandas, numpy, pyarrow
- scikit-learn, XGBoost
- SHAP
- Matplotlib for plots
- Whitenoise for static file serving
- Gunicorn for production

---

## Limitations

- The data is entirely synthetic. Performance numbers reflect internal
  consistency, not real-world accuracy.
- The generator allows only fraudulent transactions to overdraw an
  account, so balance-level features carry an unusually strong signal
  here. Real banking is messier.
- Merchant categories are drawn from a static list rather than learned
  from real merchant behaviour.
- The model does not use beneficiary/payee data, IP geolocation, or
  cross-institution signals.
- Predictions are statistical estimates and should not be used for real
  fraud decisions.

---

## License

MIT — see [LICENSE](LICENSE).