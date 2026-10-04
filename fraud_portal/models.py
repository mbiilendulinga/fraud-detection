from django.db import models


class Client(models.Model):
    client_id = models.BigIntegerField(primary_key=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)
    occupation = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    monthly_income = models.DecimalField(max_digits=14, decimal_places=2)

    client_segment = models.CharField(max_length=50)
    account_type = models.CharField(max_length=50)
    account_open_date = models.DateField()

    home_city = models.CharField(max_length=100)
    home_province = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Zambia")

    preferred_channel = models.CharField(max_length=30)

    average_monthly_transactions = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    average_monthly_spend = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    credit_score = models.PositiveIntegerField()
    client_risk_rating = models.CharField(max_length=20)

    class Meta:
        db_table = "clients"

    def __str__(self):
        return str(self.client_id)


class Transaction(models.Model):
    transaction_id = models.BigIntegerField(primary_key=True)

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    transaction_timestamp = models.DateTimeField()

    transaction_type = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default="ZMW")

    beginning_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )
    ending_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    transaction_status = models.CharField(max_length=30)

    is_fraud = models.BooleanField(default=False)

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(fields=["client", "transaction_timestamp"]),
            models.Index(fields=["transaction_timestamp"]),
            models.Index(fields=["is_fraud"]),
        ]

    def __str__(self):
        return str(self.transaction_id)


class TransactionMetadata(models.Model):
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="metadata"
    )

    channel = models.CharField(max_length=30)
    payment_method = models.CharField(max_length=30)

    merchant_id = models.CharField(max_length=40, null=True, blank=True)
    merchant_category = models.CharField(
        max_length=80,
        null=True,
        blank=True
    )

    transaction_city = models.CharField(max_length=100)
    transaction_province = models.CharField(max_length=100)
    transaction_country = models.CharField(
        max_length=100,
        default="Zambia"
    )

    device_id = models.CharField(max_length=60)
    ip_address = models.GenericIPAddressField()

    is_international = models.BooleanField(default=False)

    class Meta:
        db_table = "transaction_metadata"

    def __str__(self):
        return str(self.transaction_id)