# API

The Flask backend runs on `http://localhost:5000`. All responses are JSON. Errors look like `{"error": "Enter the farmer's name."}` with status 400, 404 or 503.

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/api/health` | Whether MongoDB can be reached |
| GET | `/api/crops` | Crop catalogue with MSP and typical yields |
| POST | `/api/assessments` | Assess a farmer and save the result (201) |
| POST | `/api/assessments?save=0` | Assess without saving (200) |
| GET | `/api/assessments?q=kolhapur` | List assessments, newest first, optionally searched by name, village or district |
| GET | `/api/assessments/<id>` | One assessment |
| DELETE | `/api/assessments/<id>` | Delete an assessment (204) |
| GET | `/api/stats` | Totals, band mix, decisions, approval rate and the model's AUC |

## Assess a farmer

Only `name`, land (`acres_owned` or `acres_leased`) and `current_crop` are required. Everything else has a sensible default.

```bash
curl -X POST http://localhost:5000/api/assessments \
  -H "Content-Type: application/json" \
  -d '{"name": "Ramesh Meena", "district": "Jaipur", "acres_owned": 3,
       "irrigation": "partial", "soil": "sandy", "season": "rabi",
       "current_crop": "Mustard", "repayment_history": "none",
       "upi_txn_per_month": 6, "shg_member": true, "requested_amount": 30000}'
```

The response includes:

- `score`, `band`, `band_meaning`, `next_band`
- `factors`: points, maximum and a note for each of the ten factors
- `risk`: `probability_of_default` and the six strongest `drivers`
- `decision`, `decision_label`, `decision_reason`, `suggested_limit`
- `finance`: this season's production, sales, cost and net, monthly income and room for a new instalment
- `actions`: steps the farmer can take, with the points each adds
- `guidance`: the best-fitting crops for the season, and whether switching would pay noticeably more

## Field values

| Field | Allowed values |
|---|---|
| `soil` | alluvial, black, red, laterite, sandy, clay |
| `irrigation` | irrigated, partial, rainfed |
| `season` | kharif, rabi |
| `repayment_history` | on_time, mostly, late, default, none |
| `tenure_months` | 6, 12 or 24 |
