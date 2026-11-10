"""The default-risk model learns the signal in its synthetic data and explains itself."""
import os

from agricred import risk_model
from agricred.assessment import clean
from profiles import GOOD, RISKY


def test_model_learns_signal():
    auc = risk_model.train(os.environ["RISK_MODEL_PATH"], n=3000)
    assert auc > 0.7


def test_drivers_are_explained():
    r = risk_model.predict(clean(RISKY))
    assert 0 < r["probability_of_default"] < 1
    assert len(r["drivers"]) == 6 and all("feature" in d for d in r["drivers"])


def test_driver_labels_describe_the_farmer():
    labels = [d["feature"] for d in risk_model.predict(clean({**GOOD, "crop_insured": False}))["drivers"]]
    assert all(isinstance(l, str) and l for l in labels)
    from agricred.risk_model import describe
    assert describe("insured", clean(GOOD)) == "Crop insured"
    assert describe("repaid_on_time", clean(RISKY)) == "Poor repayment record"
