"""Input validation, decision rules and the loan limit."""
import pytest

from agricred.assessment import ValidationError, assess, clean, decide
from profiles import GOOD, RISKY


@pytest.mark.parametrize("change,msg", [
    ({"name": ""}, "name"), ({"acres_owned": 0}, "land"), ({"current_crop": "Wheat"}, "not a kharif"),
    ({"soil": "moon"}, "soil"), ({"age": 5}, "age"),
])
def test_validation(change, msg):
    with pytest.raises(ValidationError, match=msg):
        clean({**GOOD, **change})


@pytest.mark.parametrize("band,pd_,expected", [
    ("A", 0.05, "approve"), ("A", 0.15, "conditional"), ("C", 0.05, "conditional"),
    ("B", 0.25, "review"), ("E", 0.01, "decline"), ("A", 0.4, "decline"),
])
def test_decision_rules(band, pd_, expected):
    assert decide(band, pd_)[0] == expected


def test_declined_farmer_gets_no_limit():
    r = assess(RISKY)
    if r["decision"] == "decline":
        assert r["suggested_limit"] == 0


def test_limit_respects_repayment_capacity():
    r = assess(GOOD)
    assert r["suggested_limit"] <= r["finance"]["max_new_emi"] * 12 + 1000


def test_no_capacity_means_review_not_approve():
    r = assess({**GOOD, "existing_emi": 50000})
    assert r["suggested_limit"] == 0 and r["decision"] in ("review", "decline")
    if r["decision"] == "review":
        assert "repayments" in r["decision_reason"]
