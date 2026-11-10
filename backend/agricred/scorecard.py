"""Transparent points-based credit scorecard using alternative data.

Every point can be traced to one input, so a loan officer can explain the score
to the farmer and see what would improve it. Total = 100 points.
"""

FACTORS = [
    # key, label, max points
    ("repayment", "Past repayment record", 20),
    ("debt", "Existing debt burden", 12),
    ("land", "Land and tenure", 12),
    ("irrigation", "Irrigation", 10),
    ("stability", "Harvest stability", 10),
    ("diversification", "Other income sources", 10),
    ("digital", "Digital payment activity", 8),
    ("savings", "Savings and SHG membership", 8),
    ("insurance", "Crop insurance (PMFBY)", 6),
    ("soil_card", "Soil Health Card", 4),
]
MAX_POINTS = {k: m for k, _, m in FACTORS}
LABELS = {k: label for k, label, _ in FACTORS}

BANDS = [(80, "A", "Very low risk"), (65, "B", "Low risk"), (50, "C", "Moderate risk"),
         (35, "D", "High risk"), (0, "E", "Very high risk")]


def debt_ratio(inp):
    """Monthly loan repayments as a share of average monthly household income."""
    income = monthly_income(inp)
    return inp.get("existing_emi", 0) / income if income > 0 else (1.0 if inp.get("existing_emi", 0) else 0.0)


def monthly_income(inp):
    """Farm net income spread over 12 months, plus other monthly income."""
    return max(0.0, inp.get("farm_net_income", 0) / 12 + inp.get("other_monthly_income", 0))


def _points(inp):
    pts, notes = {}, {}

    rep = inp.get("repayment_history", "none")
    pts["repayment"], notes["repayment"] = {
        "on_time": (20, "Repaid all past loans on time"),
        "mostly": (12, "Repaid past loans with a few delays"),
        "late": (5, "Frequent late repayments"),
        "default": (0, "Has defaulted on a past loan"),
        "none": (10, "No loan history yet (neutral)"),
    }[rep]

    r = debt_ratio(inp)
    if r < 0.2:
        pts["debt"], notes["debt"] = 12, f"Repayments are {r:.0%} of income"
    elif r < 0.4:
        pts["debt"], notes["debt"] = 7, f"Repayments are {r:.0%} of income"
    elif r < 0.6:
        pts["debt"], notes["debt"] = 3, f"Repayments are {r:.0%} of income, which is high"
    else:
        pts["debt"], notes["debt"] = 0, f"Repayments are {r:.0%} of income, which is very high"

    owned, leased = inp.get("acres_owned", 0), inp.get("acres_leased", 0)
    if owned >= 5:
        pts["land"] = 12
    elif owned >= 2:
        pts["land"] = 9
    elif owned > 0:
        pts["land"] = 6
    elif leased > 0 and inp.get("lease_document"):
        pts["land"] = 5
    elif leased > 0:
        pts["land"] = 2
    else:
        pts["land"] = 0
    notes["land"] = (f"Owns {owned:g} acre{'s' if owned != 1 else ''}" if owned else "Owns no land") + \
        (f", leases {leased:g} acre{'s' if leased != 1 else ''}" + (" with a written agreement" if inp.get("lease_document") else " without a written agreement") if leased else "")

    pts["irrigation"], notes["irrigation"] = {
        "irrigated": (10, "Fully irrigated"), "partial": (6, "Partly irrigated"), "rainfed": (3, "Depends on rain"),
    }[inp.get("irrigation", "rainfed")]

    f = inp.get("crop_failures_3y", 0)
    pts["stability"] = 10 if f == 0 else 6 if f == 1 else 2
    notes["stability"] = "No crop failures in 3 years" if f == 0 else f"{f} crop failure{'s' if f > 1 else ''} in 3 years"

    sources = sum(bool(inp.get(k)) for k in ("has_livestock", "other_monthly_income")) + (1 if inp.get("family_earners", 1) > 1 else 0)
    pts["diversification"] = {0: 2, 1: 6}.get(sources, 10)
    notes["diversification"] = f"{sources} income source{'s' if sources != 1 else ''} besides the main crop" if sources else "Relies on one crop only"

    t = inp.get("upi_txn_per_month", 0)
    pts["digital"] = 1 if t == 0 else 4 if t <= 10 else 7 if t <= 30 else 8
    notes["digital"] = f"About {t} UPI payments a month" if t else "No digital payments"

    pts["savings"] = (4 if inp.get("shg_member") else 0) + (4 if inp.get("regular_savings") else 0)
    parts = [p for p, ok in (("SHG member", inp.get("shg_member")), ("saves regularly", inp.get("regular_savings"))) if ok]
    text = ", ".join(parts)
    notes["savings"] = text[0].upper() + text[1:] if parts else "No SHG membership or regular savings"

    pts["insurance"] = 6 if inp.get("crop_insured") else 0
    notes["insurance"] = "Crop insured under PMFBY" if inp.get("crop_insured") else "Crop not insured"

    pts["soil_card"] = 4 if inp.get("soil_health_card") else 0
    notes["soil_card"] = "Has a Soil Health Card" if inp.get("soil_health_card") else "No Soil Health Card"
    return pts, notes


def band(score):
    for cutoff, letter, meaning in BANDS:
        if score >= cutoff:
            return letter, meaning
    return "E", "Very high risk"


def score(inp):
    pts, notes = _points(inp)
    total = sum(pts.values())
    letter, meaning = band(total)
    factors = [{
        "key": k, "label": LABELS[k], "points": pts[k], "max": MAX_POINTS[k], "note": notes[k],
        "gap": MAX_POINTS[k] - pts[k],
    } for k, _, _ in FACTORS]
    higher = [(c, l) for c, l, _ in BANDS if c > total]
    next_band = {"band": higher[-1][1], "points_needed": higher[-1][0] - total} if higher else None
    return {"score": total, "band": letter, "band_meaning": meaning, "factors": factors, "next_band": next_band}
