from decimal import Decimal
import datetime

from django import forms


TRANSACTION_TYPES = [
    ("Purchase", "Purchase"),
    ("Transfer", "Transfer"),
    ("Withdrawal", "Withdrawal"),
    ("Deposit", "Deposit"),
    ("Bill Payment", "Bill Payment"),
    ("Card Payment", "Card Payment"),
]

CHANNELS = [
    ("Mobile Banking", "Mobile Banking"),
    ("Online Banking", "Online Banking"),
    ("POS", "Point of Sale"),
    ("ATM", "ATM"),
    ("Branch", "Branch"),
]

PAYMENT_METHODS = [
    ("Debit Card", "Debit Card"),
    ("Credit Card", "Credit Card"),
    ("Bank Transfer", "Bank Transfer"),
    ("Mobile Money", "Mobile Money"),
    ("Cash", "Cash"),
]

SEGMENTS = [
    ("Mass Market", "Mass Market"),
    ("Emerging Affluent", "Emerging Affluent"),
    ("Affluent", "Affluent"),
    ("Premium", "Premium"),
]

RISK_RATINGS = [
    ("Low", "Low"),
    ("Medium", "Medium"),
    ("High", "High"),
]

PROVINCES = [
    ("Lusaka", "Lusaka"),
    ("Copperbelt", "Copperbelt"),
    ("Central", "Central"),
    ("Southern", "Southern"),
    ("Eastern", "Eastern"),
    ("Northern", "Northern"),
    ("Luapula", "Luapula"),
    ("Western", "Western"),
    ("North-Western", "North-Western"),
    ("Muchinga", "Muchinga"),
]

COUNTRIES = [
    ("Zambia", "Zambia"),
    ("South Africa", "South Africa"),
    ("Botswana", "Botswana"),
    ("Zimbabwe", "Zimbabwe"),
    ("Tanzania", "Tanzania"),
    ("United Kingdom", "United Kingdom"),
    ("United States", "United States"),
    ("United Arab Emirates", "United Arab Emirates"),
]


class TransactionForm(forms.Form):
    # ---- Transaction --------------------------------------------
    amount = forms.DecimalField(
        label="Amount (ZMW)",
        min_value=Decimal("1"),
        max_value=Decimal("500000"),
        initial=Decimal("1200"),
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )
    transaction_type = forms.ChoiceField(
        label="Transaction type",
        choices=TRANSACTION_TYPES,
        initial="Purchase",
    )
    channel = forms.ChoiceField(
        label="Channel",
        choices=CHANNELS,
        initial="Mobile Banking",
    )
    payment_method = forms.ChoiceField(
        label="Payment method",
        choices=PAYMENT_METHODS,
        initial="Mobile Money",
    )
    transaction_hour = forms.IntegerField(
        label="Hour of day (0–23)",
        min_value=0,
        max_value=23,
        initial=14,
    )
    is_weekend = forms.BooleanField(
        label="Weekend transaction",
        required=False,
    )
    is_international = forms.BooleanField(
        label="International transaction",
        required=False,
    )
    transaction_country = forms.ChoiceField(
        label="Transaction country",
        choices=COUNTRIES,
        initial="Zambia",
    )
    transaction_province = forms.ChoiceField(
        label="Transaction province",
        choices=PROVINCES,
        initial="Lusaka",
    )

    # ---- Customer -----------------------------------------------
    home_province = forms.ChoiceField(
        label="Customer home province",
        choices=PROVINCES,
        initial="Lusaka",
    )
    client_segment = forms.ChoiceField(
        label="Customer segment",
        choices=SEGMENTS,
        initial="Mass Market",
    )
    client_risk_rating = forms.ChoiceField(
        label="Customer risk rating",
        choices=RISK_RATINGS,
        initial="Low",
    )
    monthly_income = forms.DecimalField(
        label="Monthly income (ZMW)",
        min_value=Decimal("500"),
        max_value=Decimal("1000000"),
        initial=Decimal("8500"),
    )
    avg_monthly_spend = forms.DecimalField(
        label="Average monthly spend (ZMW)",
        min_value=Decimal("0"),
        max_value=Decimal("1000000"),
        initial=Decimal("5400"),
    )
    avg_monthly_transactions = forms.IntegerField(
        label="Average monthly transactions",
        min_value=1,
        max_value=300,
        initial=25,
    )

    # ---- Recent behaviour ---------------------------------------
    is_new_device = forms.BooleanField(
        label="Transaction made from a new device",
        required=False,
    )
    transactions_last_1h = forms.IntegerField(
        label="Transactions in the last 1 hour",
        min_value=0,
        max_value=100,
        initial=0,
    )
    transactions_last_24h = forms.IntegerField(
        label="Transactions in the last 24 hours",
        min_value=0,
        max_value=500,
        initial=2,
    )
    is_new_transaction_province = forms.BooleanField(
        label="First time transacting in this province",
        required=False,
    )

    # ------------------------------------------------------------
    # Derive a complete payload for the predictor.
    # ------------------------------------------------------------
    def to_payload(self) -> dict:
        d = self.cleaned_data

        amount = float(d["amount"])
        income = float(d["monthly_income"])
        spend = float(d["avg_monthly_spend"])
        hour = int(d["transaction_hour"])
        weekend = 1 if d["is_weekend"] else 0

        is_night = 1 if (hour < 6 or hour >= 22) else 0
        is_business = 1 if (9 <= hour < 17 and not weekend) else 0

        location_match = (
            1 if d["transaction_province"] == d["home_province"] else 0
        )

        payload = {
            # transaction
            "amount": amount,
            "transaction_type": d["transaction_type"],
            "currency": "ZMW",
            "transaction_hour": hour,
            "transaction_day_of_week": (
                (datetime.date.today().weekday() + 0) % 7
            ),
            "transaction_day_of_month": datetime.date.today().day,
            "transaction_month": datetime.date.today().month,
            "is_weekend": weekend,
            "is_night": is_night,
            "is_business_hours": is_business,

            # channel / metadata
            "channel": d["channel"],
            "payment_method": d["payment_method"],
            "transaction_country": d["transaction_country"],
            "transaction_province": d["transaction_province"],
            "is_international": 1 if d["is_international"] else 0,

            # customer
            "home_province": d["home_province"],
            "client_segment": d["client_segment"],
            "client_risk_rating": d["client_risk_rating"],
            "monthly_income": income,
            "avg_monthly_spend": spend,
            "avg_monthly_transactions": int(d["avg_monthly_transactions"]),
            "preferred_channel": d["channel"],

            # interaction
            "amount_vs_monthly_income": amount / income if income else 0,
            "amount_vs_monthly_spend": amount / spend if spend else 0,
            "location_matches_home_province": location_match,

            # velocity / novelty
            "is_new_device": 1 if d["is_new_device"] else 0,
            "transactions_last_1h": int(d["transactions_last_1h"]),
            "transactions_last_24h": int(d["transactions_last_24h"]),
            "is_new_transaction_province": (
                1 if d["is_new_transaction_province"] else 0
            ),
        }

        # Reasonable defaults for features the form doesn't collect.
        # The predictor leaves anything missing as NaN (XGBoost handles it),
        # but supplying sensible values keeps predictions stable.
        payload.setdefault("transactions_last_10min", 0)
        payload.setdefault("transactions_last_6h",
                           payload["transactions_last_1h"])
        payload.setdefault("transactions_last_7d",
                           payload["transactions_last_24h"] * 4)
        payload.setdefault("amount_last_1h",
                           payload["transactions_last_1h"] * amount)
        payload.setdefault("amount_last_6h",
                           payload["transactions_last_1h"] * amount)
        payload.setdefault("amount_last_24h",
                           payload["transactions_last_24h"] * amount)
        payload.setdefault("amount_last_7d",
                           payload["transactions_last_24h"] * amount * 4)
        payload.setdefault(
            "average_amount_last_24h",
            payload["amount_last_24h"] /
            max(payload["transactions_last_24h"], 1),
        )
        payload.setdefault("maximum_amount_last_24h", amount)
        payload.setdefault("is_low_balance_after_transaction", 0)
        payload.setdefault("is_overdrawn", 0)
        payload.setdefault("is_new_transaction_city",
                           payload["is_new_transaction_province"])
        payload.setdefault("amount_vs_customer_average", 1.0)
        payload.setdefault("amount_vs_customer_median", 1.0)
        payload.setdefault("customer_amount_zscore", 0.0)
        payload.setdefault("is_new_merchant", 0)
        payload.setdefault("device_change_from_previous",
                           payload["is_new_device"])
        payload.setdefault("channel_change_from_previous", 0)
        payload.setdefault("merchant_change_from_previous", 0)
        payload.setdefault("location_change_from_previous", 0)
        payload.setdefault("province_change_from_previous",
                           payload["is_new_transaction_province"])
        payload.setdefault("time_since_previous_transaction_seconds", 3600)
        payload.setdefault("amount_change_from_previous", 0)
        payload.setdefault("amount_ratio_from_previous", 1.0)
        payload.setdefault("transaction_type_changed", 0)

        return payload