"""The 100-point scorecard: every point is explained and adds up."""
from agricred import scorecard
from agricred.assessment import assess
from profiles import GOOD, RISKY


def test_scorecard_max_is_100():
    assert sum(scorecard.MAX_POINTS.values()) == 100


def test_good_profile_scores_high_and_risky_low():
    good, risky = assess(GOOD), assess(RISKY)
    assert good["band"] in ("A", "B") and good["decision"] in ("approve", "conditional")
    assert risky["band"] in ("D", "E") and risky["decision"] in ("review", "decline")
    assert good["risk"]["probability_of_default"] < risky["risk"]["probability_of_default"]


def test_every_point_is_explained():
    r = assess(GOOD)
    assert sum(f["points"] for f in r["factors"]) == r["score"]
    assert all(f["note"] for f in r["factors"])


def test_insurance_adds_six_points():
    base = assess({**GOOD, "crop_insured": False})["score"]
    assert assess(GOOD)["score"] - base == 6


def test_notes_grammar_and_next_band():
    r = assess({**GOOD, "acres_owned": 1, "acres_leased": 1, "lease_document": True, "regular_savings": False})
    land = next(f for f in r["factors"] if f["key"] == "land")["note"]
    savings = next(f for f in r["factors"] if f["key"] == "savings")["note"]
    assert "1 acre," in land and "leases 1 acre " in land and savings == "SHG member"
    if r["band"] != "A":
        assert r["next_band"]["points_needed"] > 0
