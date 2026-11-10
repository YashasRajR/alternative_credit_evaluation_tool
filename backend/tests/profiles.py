"""Two sample farmers shared by the tests: a strong borrower and a risky one."""

GOOD = dict(name="Lakshmi", village="Hosur", district="Mysuru", state="Karnataka", acres_owned=4,
            irrigation="irrigated", soil="red", season="kharif", current_crop="Ragi",
            repayment_history="on_time", upi_txn_per_month=25, other_monthly_income=8000,
            has_livestock=True, shg_member=True, regular_savings=True, crop_insured=True,
            soil_health_card=True, years_farming=15, requested_amount=40000)
RISKY = dict(name="Suresh", acres_leased=1.5, irrigation="rainfed", soil="sandy", season="kharif",
             current_crop="Bajra", repayment_history="default", crop_failures_3y=2,
             existing_emi=6000, years_farming=3)
