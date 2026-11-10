# The default-risk model

## What it does

A logistic regression estimates the chance that a farmer will not repay. It sits beside the scorecard as a second opinion: the scorecard is a fixed, explainable rule, and the model weighs the same kind of information statistically.

Logistic regression was chosen because each feature's effect can be shown. On the result page, "What the risk model weighed" lists the six features that moved this farmer's risk most, compared with a typical borrower.

## Features

| Feature | Meaning |
|---|---|
| Past repayment record | On time 1, a few delays 0.6, no history 0.5, often late 0.2, defaulted 0 |
| Previous default | 1 if the farmer has defaulted |
| Debt burden | Existing repayments as a share of income, capped at 1.5 |
| Farm size | Log of acres cultivated |
| Owns land | 1 if any land is owned |
| Irrigation | Rain-fed 0, partly irrigated 1, irrigated 2 |
| Recent crop failures | Failures in the last 3 years |
| Other income sources | Count of: livestock, other income, more than one earner |
| Digital payments | Log of UPI payments a month |
| SHG membership, Regular savings, Crop insurance | 1 or 0 |
| Farming experience | Years |

## Training data is synthetic

There is no public dataset of loan outcomes for Indian smallholder farmers. `risk_model.py` therefore generates 6,000 labelled farmers. Each farmer's chance of default comes from fixed relationships plus random noise. For example, high debt and a past default raise risk, and irrigation and on-time repayment lower it.

The model learns those relationships back. On held-out synthetic data it reaches an AUC of about 0.72. That shows the method works. It says nothing about real-world accuracy.

**Before a lender relies on it**, replace `synthetic_dataset()` with the institution's own loan history and retrain. The rest of the app does not need to change.

## Files

- Trained model: `backend/models/risk_model.joblib`. It is created on first start and is not committed to git.
- Delete that file to retrain. Set `RISK_MODEL_PATH` to keep it somewhere else.
