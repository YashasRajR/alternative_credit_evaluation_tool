"""Crop catalogue, MSP economics and crop guidance."""
from agricred import crops


def test_no_paddy_for_rainfed_sandy_land():
    names = [c["crop"] for c in crops.recommend("kharif", "sandy", "rainfed")]
    assert "Paddy" not in names and names


def test_rabi_recommendations_are_rabi_crops():
    for c in crops.recommend("rabi", "alluvial", "irrigated"):
        assert crops.CROPS[c["crop"]]["season"] == "rabi"


def test_economics_uses_overrides():
    e = crops.economics("Wheat", 2, yield_per_acre=10, price=3000)
    assert e["gross"] == 60000 and e["production_qtl"] == 20
