"""Crop catalogue and crop guidance.

Prices are Minimum Support Prices (MSP) announced by the Government of India:
  Kharif crops: Kharif Marketing Season 2026-27
  Rabi crops:   Rabi Marketing Season 2027-28
Costs are CACP all-India average costs of production (A2+FL) per quintal from the
same announcements where published; where not published (soybean, cotton,
mustard) the cost is estimated as MSP / 1.5, since MSP is set at least 50% above cost.
Yields are typical all-India averages and vary a lot by district: the app lets
the user override yield and price. Update these numbers each season.
"""

PRICE_SOURCE = "MSP: Kharif 2026-27, Rabi 2027-28 (Government of India). Yields are typical all-India averages."

# name: season, suitable soils, water need, MSP (Rs/qtl), cost (Rs/qtl), typical yield (qtl/acre)
CROPS = {
    "Paddy":      dict(season="kharif", soils=["alluvial", "clay", "laterite"], water="high", msp=2441, cost=1627, yield_=11.0),
    "Maize":      dict(season="kharif", soils=["alluvial", "red", "black"], water="medium", msp=2410, cost=1508, yield_=13.0),
    "Jowar":      dict(season="kharif", soils=["black", "red", "alluvial"], water="low", msp=4023, cost=2682, yield_=4.0),
    "Bajra":      dict(season="kharif", soils=["sandy", "red", "alluvial"], water="low", msp=2900, cost=1703, yield_=6.0),
    "Ragi":       dict(season="kharif", soils=["red", "laterite", "sandy"], water="low", msp=5205, cost=3257, yield_=7.0),
    "Tur (Arhar)": dict(season="kharif", soils=["black", "red", "alluvial"], water="low", msp=8450, cost=5496, yield_=3.5),
    "Moong":      dict(season="kharif", soils=["alluvial", "red", "sandy"], water="low", msp=8780, cost=5438, yield_=2.5),
    "Urad":       dict(season="kharif", soils=["black", "alluvial", "clay"], water="low", msp=8200, cost=5418, yield_=2.7),
    "Groundnut":  dict(season="kharif", soils=["sandy", "red", "alluvial"], water="medium", msp=7517, cost=5011, yield_=7.0),
    "Soybean":    dict(season="kharif", soils=["black", "alluvial"], water="medium", msp=5708, cost=3805, yield_=4.5),
    "Cotton":     dict(season="kharif", soils=["black", "alluvial"], water="medium", msp=8267, cost=5512, yield_=5.5),
    "Wheat":      dict(season="rabi", soils=["alluvial", "black", "clay"], water="medium", msp=2610, cost=1264, yield_=14.0),
    "Barley":     dict(season="rabi", soils=["alluvial", "sandy"], water="low", msp=2286, cost=1361, yield_=11.0),
    "Gram (Chana)": dict(season="rabi", soils=["black", "alluvial", "red"], water="low", msp=5958, cost=3699, yield_=4.5),
    "Lentil (Masur)": dict(season="rabi", soils=["alluvial", "clay", "black"], water="low", msp=7390, cost=3705, yield_=4.0),
    "Mustard":    dict(season="rabi", soils=["alluvial", "sandy"], water="low", msp=6613, cost=3212, yield_=6.0),
}

SOILS = ["alluvial", "black", "red", "laterite", "sandy", "clay"]
WATER_LEVEL = {"irrigated": 3, "partial": 2, "rainfed": 1}
NEED_LEVEL = {"low": 1, "medium": 2, "high": 3}


def economics(crop, acres, yield_per_acre=None, price=None):
    """Expected gross income, cultivation cost and net income for a crop."""
    c = CROPS[crop]
    y = yield_per_acre if yield_per_acre else c["yield_"]
    p = price if price else c["msp"]
    production = y * acres
    gross = production * p
    cost = c["cost"] * c["yield_"] * acres  # cultivation cost per acre does not depend on this year's yield
    return {
        "crop": crop, "acres": acres, "yield_per_acre": round(y, 1), "price": p,
        "production_qtl": round(production, 1), "gross": round(gross), "cost": round(cost),
        "net": round(gross - cost), "net_per_acre": round((gross - cost) / acres) if acres else 0,
    }


def recommend(season, soil, irrigation, current_crop=None, top=3):
    """Rank crops for the farm by suitability, then by expected profit per acre."""
    water = WATER_LEVEL.get(irrigation, 1)
    ranked = []
    for name, c in CROPS.items():
        if c["season"] != season:
            continue
        reasons, fit = [], 0
        if soil in c["soils"]:
            fit += 2
            reasons.append(f"suits {soil} soil")
        need = NEED_LEVEL[c["water"]]
        if need <= water:
            fit += 2
            reasons.append("water need matches your irrigation" if need > 1 else "needs little water")
        elif need - water == 1:
            fit += 1
            reasons.append("needs more water than you have in a dry year")
        else:
            continue  # e.g. paddy on rainfed land: too risky to recommend
        per_acre = economics(name, 1)
        ranked.append({
            "crop": name, "fit": fit, "reasons": reasons,
            "msp": c["msp"], "yield_per_acre": c["yield_"],
            "net_per_acre": per_acre["net_per_acre"],
            "is_current": name == current_crop,
        })
    ranked.sort(key=lambda r: (r["fit"], r["net_per_acre"]), reverse=True)
    return ranked[:top]
