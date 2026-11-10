"""Probability-of-default model.

There is no public dataset of Indian smallholder loan outcomes, so the model is
trained on SYNTHETIC data. The data generator below encodes plausible
relationships (e.g. irrigation and on-time repayment lower risk, high debt raises
it) plus random noise. The model therefore demonstrates the method, not real-world
accuracy: replace `synthetic_dataset` with your institution's historical loans
before using it for decisions.

A logistic regression is used on purpose: each feature's contribution to the
prediction can be shown to the loan officer.
"""
import os

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .scorecard import debt_ratio

MODEL_PATH = os.getenv("RISK_MODEL_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "risk_model.joblib"))

FEATURES = [
    ("repaid_on_time", "Past repayment record"),
    ("defaulted_before", "Previous default"),
    ("debt_ratio", "Debt burden"),
    ("log_acres", "Farm size"),
    ("owns_land", "Owns land"),
    ("irrigation", "Irrigation"),
    ("crop_failures", "Recent crop failures"),
    ("income_sources", "Other income sources"),
    ("upi_activity", "Digital payments"),
    ("shg_member", "SHG membership"),
    ("saves", "Regular savings"),
    ("insured", "Crop insurance"),
    ("years_farming", "Farming experience"),
]
FEATURE_NAMES = [f for f, _ in FEATURES]
FEATURE_LABELS = dict(FEATURES)

# Relationships used to generate synthetic outcomes (log-odds per unit).
_TRUE_COEF = {
    "repaid_on_time": -1.4, "defaulted_before": 1.6, "debt_ratio": 2.2,
    "log_acres": -0.35, "owns_land": -0.4, "irrigation": -0.45, "crop_failures": 0.55,
    "income_sources": -0.35, "upi_activity": -0.25, "shg_member": -0.35, "saves": -0.3,
    "insured": -0.4, "years_farming": -0.02,
}
_INTERCEPT = -1.0

# No history is treated as neutral: between "a few delays" and "often late".
REPAY_LEVEL = {"on_time": 1.0, "mostly": 0.6, "none": 0.5, "late": 0.2, "default": 0.0}


def describe(feature, inp):
    """Plain-language description of this farmer's value for a model feature."""
    rep = inp.get("repayment_history", "none")
    acres = inp.get("acres_owned", 0) + inp.get("acres_leased", 0)
    n_fail = inp.get("crop_failures_3y", 0)
    upi = inp.get("upi_txn_per_month", 0)
    return {
        "repaid_on_time": {"on_time": "Repaid past loans on time", "mostly": "Repaid with a few delays",
                           "none": "No loan history", "late": "Often late with repayments",
                           "default": "Poor repayment record"}[rep],
        "defaulted_before": "Has defaulted before" if rep == "default" else "No past default",
        "debt_ratio": f"Existing repayments: {debt_ratio(inp):.0%} of income",
        "log_acres": f"Farms {acres:g} acre{'s' if acres != 1 else ''}",
        "owns_land": "Owns land" if inp.get("acres_owned", 0) > 0 else "Owns no land",
        "irrigation": {"irrigated": "Irrigated land", "partial": "Partly irrigated", "rainfed": "Rain-fed only"}[inp.get("irrigation", "rainfed")],
        "crop_failures": "No recent crop failures" if n_fail == 0 else f"{n_fail} crop failure{'s' if n_fail > 1 else ''} in 3 years",
        "income_sources": "Has other income sources" if featurize(inp)[7] > 0 else "Only farm income",
        "upi_activity": f"About {upi} UPI payments a month" if upi else "No digital payments",
        "shg_member": "SHG member" if inp.get("shg_member") else "Not in an SHG",
        "saves": "Saves regularly" if inp.get("regular_savings") else "No regular savings",
        "insured": "Crop insured" if inp.get("crop_insured") else "Crop not insured",
        "years_farming": f"{inp.get('years_farming', 0)} years of farming",
    }[feature]


def featurize(inp):
    rep = inp.get("repayment_history", "none")
    sources = sum(bool(inp.get(k)) for k in ("has_livestock", "other_monthly_income")) + (1 if inp.get("family_earners", 1) > 1 else 0)
    return np.array([
        REPAY_LEVEL[rep],
        1.0 if rep == "default" else 0.0,
        min(debt_ratio(inp), 1.5),
        np.log1p(inp.get("acres_owned", 0) + inp.get("acres_leased", 0)),
        1.0 if inp.get("acres_owned", 0) > 0 else 0.0,
        {"rainfed": 0.0, "partial": 1.0, "irrigated": 2.0}[inp.get("irrigation", "rainfed")],
        float(inp.get("crop_failures_3y", 0)),
        float(sources),
        np.log1p(inp.get("upi_txn_per_month", 0)),
        1.0 if inp.get("shg_member") else 0.0,
        1.0 if inp.get("regular_savings") else 0.0,
        1.0 if inp.get("crop_insured") else 0.0,
        float(inp.get("years_farming", 0)),
    ])


def synthetic_dataset(n=6000, seed=7):
    """Generate n synthetic farmer profiles and default outcomes."""
    rng = np.random.default_rng(seed)
    rep = rng.choice(["on_time", "mostly", "late", "default", "none"], n, p=[0.35, 0.2, 0.1, 0.05, 0.3])
    X = np.column_stack([
        np.vectorize(REPAY_LEVEL.get)(rep).astype(float),
        (rep == "default").astype(float),
        np.clip(rng.gamma(2.0, 0.12, n), 0, 1.5),
        np.log1p(rng.gamma(1.6, 1.5, n)),
        rng.binomial(1, 0.7, n).astype(float),
        rng.choice([0.0, 1.0, 2.0], n, p=[0.45, 0.3, 0.25]),
        rng.choice([0.0, 1.0, 2.0, 3.0], n, p=[0.55, 0.28, 0.12, 0.05]),
        rng.choice([0.0, 1.0, 2.0, 3.0], n, p=[0.3, 0.4, 0.22, 0.08]),
        np.log1p(rng.choice([0, 3, 12, 40], n, p=[0.3, 0.3, 0.25, 0.15]) * rng.uniform(0.7, 1.3, n)),
        rng.binomial(1, 0.35, n).astype(float),
        rng.binomial(1, 0.4, n).astype(float),
        rng.binomial(1, 0.3, n).astype(float),
        rng.integers(1, 40, n).astype(float),
    ])
    coef = np.array([_TRUE_COEF[f] for f in FEATURE_NAMES])
    logit = _INTERCEPT + X @ coef + rng.normal(0, 0.6, n)
    y = rng.binomial(1, 1 / (1 + np.exp(-logit)))
    return X, y


def train(path=MODEL_PATH, n=6000, seed=7):
    X, y = synthetic_dataset(n, seed)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    model.fit(Xtr, ytr)
    auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump({"model": model, "auc": float(auc), "default_rate": float(y.mean()), "n": n}, path)
    return auc


_cache = {}


def load(path=MODEL_PATH):
    if path not in _cache:
        if not os.path.exists(path):
            train(path)
        _cache[path] = joblib.load(path)
    return _cache[path]


def predict(inp, path=MODEL_PATH):
    """Return probability of default and each feature's contribution (in log-odds)."""
    bundle = load(path)
    model = bundle["model"]
    x = featurize(inp).reshape(1, -1)
    pd_ = float(model.predict_proba(x)[0, 1])
    scaler, lr = model.named_steps["standardscaler"], model.named_steps["logisticregression"]
    contrib = ((x - scaler.mean_) / scaler.scale_)[0] * lr.coef_[0]
    drivers = sorted(
        [{"feature": describe(f, inp), "effect": round(float(c), 3)} for f, c in zip(FEATURE_NAMES, contrib)],
        key=lambda d: abs(d["effect"]), reverse=True,
    )
    return {"probability_of_default": round(pd_, 4), "drivers": drivers[:6], "model_auc": round(bundle["auc"], 3)}
