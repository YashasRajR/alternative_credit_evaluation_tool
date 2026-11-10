"""Combine the scorecard, risk model and crop economics into one credit assessment."""
from datetime import datetime, timezone

from . import crops, risk_model, scorecard

BAND_LIMIT_FACTOR = {"A": 1.0, "B": 0.9, "C": 0.75, "D": 0.5, "E": 0.0}
MAX_EMI_SHARE = 0.4  # total loan repayments should stay under 40% of monthly income


class ValidationError(ValueError):
    pass


def _num(d, key, default=0, lo=0, hi=None, cast=float):
    v = d.get(key, default)
    if v in ("", None):
        v = default
    try:
        v = cast(v)
    except (TypeError, ValueError):
        raise ValidationError(f"{key} must be a number")
    if v < lo or (hi is not None and v > hi):
        raise ValidationError(f"{key} must be between {lo} and {hi}" if hi is not None else f"{key} must be at least {lo}")
    return v


def clean(data):
    """Validate and normalise raw form input."""
    if not str(data.get("name", "")).strip():
        raise ValidationError("Farmer's name is required")
    out = {
        "name": str(data["name"]).strip()[:80],
        "village": str(data.get("village", "")).strip()[:80],
        "district": str(data.get("district", "")).strip()[:80],
        "state": str(data.get("state", "")).strip()[:80],
        "age": _num(data, "age", 40, 18, 100, int),
        "family_size": _num(data, "family_size", 4, 1, 30, int),
        "family_earners": _num(data, "family_earners", 1, 1, 20, int),
        "acres_owned": _num(data, "acres_owned", 0, 0, 500),
        "acres_leased": _num(data, "acres_leased", 0, 0, 500),
        "lease_document": bool(data.get("lease_document")),
        "soil": data.get("soil", "alluvial"),
        "irrigation": data.get("irrigation", "rainfed"),
        "season": data.get("season", "kharif"),
        "current_crop": data.get("current_crop", ""),
        "crops_per_year": _num(data, "crops_per_year", 1, 1, 3, int),
        "expected_yield": _num(data, "expected_yield", 0, 0, 200),
        "expected_price": _num(data, "expected_price", 0, 0, 100000),
        "years_farming": _num(data, "years_farming", 5, 0, 80, int),
        "crop_failures_3y": _num(data, "crop_failures_3y", 0, 0, 3, int),
        "has_livestock": bool(data.get("has_livestock")),
        "other_monthly_income": _num(data, "other_monthly_income", 0, 0, 10_000_000),
        "existing_emi": _num(data, "existing_emi", 0, 0, 10_000_000),
        "repayment_history": data.get("repayment_history", "none"),
        "shg_member": bool(data.get("shg_member")),
        "regular_savings": bool(data.get("regular_savings")),
        "upi_txn_per_month": _num(data, "upi_txn_per_month", 0, 0, 10000, int),
        "crop_insured": bool(data.get("crop_insured")),
        "soil_health_card": bool(data.get("soil_health_card")),
        "requested_amount": _num(data, "requested_amount", 0, 0, 100_000_000),
        "tenure_months": _num(data, "tenure_months", 12, 3, 120, int),
    }
    if out["acres_owned"] + out["acres_leased"] <= 0:
        raise ValidationError("Enter the land farmed (owned or leased acres)")
    checks = {
        "soil": crops.SOILS, "irrigation": list(crops.WATER_LEVEL), "season": ["kharif", "rabi"],
        "repayment_history": ["on_time", "mostly", "late", "default", "none"],
    }
    for key, allowed in checks.items():
        if out[key] not in allowed:
            raise ValidationError(f"{key} must be one of: {', '.join(allowed)}")
    if out["current_crop"] not in crops.CROPS:
        raise ValidationError("Choose the crop being grown")
    if crops.CROPS[out["current_crop"]]["season"] != out["season"]:
        raise ValidationError(f"{out['current_crop']} is not a {out['season']} crop")
    return out


def decide(band, pd_):
    if band == "E" or pd_ >= 0.35:
        return "decline", "Decline for now"
    if band == "D" or pd_ >= 0.2:
        return "review", "Refer for field review"
    if band == "C" or pd_ >= 0.1:
        return "conditional", "Approve with conditions"
    return "approve", "Approve"


def improvement_actions(factors, inp):
    """Concrete steps the farmer can take, with the score points each would add."""
    actions = []
    gaps = {f["key"]: f["gap"] for f in factors}
    if gaps["insurance"]:
        actions.append(("Enrol the crop in PMFBY crop insurance", gaps["insurance"],
                        "Protects income if the harvest fails, which also protects the loan."))
    if gaps["soil_card"]:
        actions.append(("Get a Soil Health Card", gaps["soil_card"],
                        "Free soil test through the state agriculture department; shows the right fertiliser use."))
    if gaps["savings"]:
        actions.append(("Join a Self-Help Group or start regular savings", gaps["savings"],
                        "Regular small deposits build a record of repayment discipline."))
    if gaps["digital"] >= 4:
        actions.append(("Receive and make payments by UPI", gaps["digital"] - 1,
                        "Digital payments create a verifiable record of income and spending."))
    if gaps["debt"] >= 5:
        actions.append(("Reduce existing loan repayments", gaps["debt"],
                        "Clearing a costly informal loan first frees up repayment capacity."))
    if gaps["land"] and inp["acres_leased"] and not inp["lease_document"]:
        actions.append(("Get a written lease agreement", 3, "A registered or written lease proves cultivation rights."))
    return [{"action": a, "points": p, "why": w} for a, p, w in sorted(actions, key=lambda x: -x[1])]


def assess(raw):
    inp = clean(raw)
    acres = inp["acres_owned"] + inp["acres_leased"]
    econ = crops.economics(inp["current_crop"], acres, inp["expected_yield"] or None, inp["expected_price"] or None)
    inp["farm_net_income"] = econ["net"] * inp["crops_per_year"]

    sc = scorecard.score(inp)
    risk = risk_model.predict(inp)
    decision, decision_label = decide(sc["band"], risk["probability_of_default"])

    monthly = scorecard.monthly_income(inp)
    emi_room = max(0.0, MAX_EMI_SHARE * monthly - inp["existing_emi"])
    need = econ["cost"] * inp["crops_per_year"] * 1.3  # cultivation cost + 30% for post-harvest and upkeep
    capacity = emi_room * inp["tenure_months"]
    limit = round(min(need, capacity) * BAND_LIMIT_FACTOR[sc["band"]] / 1000) * 1000
    reason = None
    if decision == "decline":
        limit = 0
    elif limit == 0:
        # A good record but no room to repay: approving would set the farmer up to fail.
        decision, decision_label = "review", "Refer for field review"
        reason = "Existing loan repayments already use up the income available for a new loan."

    guidance = crops.recommend(inp["season"], inp["soil"], inp["irrigation"], inp["current_crop"])
    current_net = econ["net_per_acre"]
    best = guidance[0] if guidance else None
    switch = None
    if best and best["crop"] != inp["current_crop"] and best["net_per_acre"] > current_net * 1.1:
        switch = {"crop": best["crop"], "extra_per_acre": best["net_per_acre"] - current_net,
                  "extra_total": (best["net_per_acre"] - current_net) * acres}

    return {
        "farmer": {k: inp[k] for k in ("name", "village", "district", "state", "age", "family_size")},
        "inputs": inp,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "score": sc["score"], "band": sc["band"], "band_meaning": sc["band_meaning"], "next_band": sc["next_band"],
        "factors": sc["factors"],
        "risk": risk,
        "decision": decision, "decision_label": decision_label, "decision_reason": reason,
        "suggested_limit": limit,
        "requested_amount": inp["requested_amount"],
        "finance": {
            "monthly_income": round(monthly), "debt_ratio": round(scorecard.debt_ratio(inp), 3),
            "max_new_emi": round(emi_room), "cultivation_need": round(need),
            "season": econ, "annual_farm_net": round(inp["farm_net_income"]),
        },
        "guidance": {"crops": guidance, "switch": switch, "source": crops.PRICE_SOURCE},
        "actions": improvement_actions(sc["factors"], inp),
    }
