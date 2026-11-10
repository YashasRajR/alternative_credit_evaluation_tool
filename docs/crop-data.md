# Crop data

`backend/agricred/crops.py` holds one row per crop: season, suitable soils, water need, MSP, cost of production and typical yield.

| Season | Crops |
|---|---|
| Kharif (MSP 2026-27) | Paddy, Maize, Jowar, Bajra, Ragi, Tur (Arhar), Moong, Urad, Groundnut, Soybean, Cotton |
| Rabi (MSP 2027-28) | Wheat, Barley, Gram (Chana), Lentil (Masur), Mustard |

## Where the numbers come from

- **MSP** (₹ per quintal): the Government of India's announced Minimum Support Prices for Kharif 2026-27 and Rabi 2027-28.
- **Cost** (₹ per quintal): CACP's A2+FL cost of production, as published alongside the MSP.
- **Yield** (quintal per acre): typical all-India averages. Real yields vary widely by district and year, so the form lets the loan officer enter the local yield and price instead.

## How guidance is ranked

For the farm's season, each crop gets fit points: 2 if it suits the soil, and 2 if its water need is met by the farm's irrigation, or 1 if it needs one level more. Crops that need two levels more water than the farm has, such as paddy on rain-fed land, are left out because they are too risky to recommend. The rest are ranked by fit, then by net income per acre at MSP.

If the best crop would earn more than 10% more per acre than the current one, the result page suggests the switch and shows the extra income across the farm.

## Updating each season

When new MSPs are announced, update `msp` and `cost` in `CROPS` and the `PRICE_SOURCE` line, then run `pytest` in `backend`.
