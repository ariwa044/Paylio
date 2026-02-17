from django.db import models
from shortuuid.django_fields import ShortUUIDField
from userauths.models import User
from account.models import Account
from django.utils import timezone

# Create your models here.

TRANSACTION_TYPE = (
    ("deposit", "Deposit"),
    ("transfer", "Transfer"),
    ("received", "Received"),
    ("withdraw", "Withdrawal"),
    ("refund", "Refund"),
    ("request", "Payment Request"),
    ("none", "None")
)

CRYPTO_CURRENCIES = (
    ("BTC", "Bitcoin"),
    ("ETH", "Ethereum"),
    ("USDT", "Tether"),
    ("BNB", "Binance Coin"),
)

DEPOSIT_METHOD = (
    ("bank_transfer", "Bank Transfer"),
    ("card_payment", "Card Payment"),
    ("saved_card", "Saved Card"),
)

TRANSACTION_STATUS = (
    ("failed", "failed"),
    ("completed", "completed"),
    ("pending", "pending"),
    ("processing", "processing"),
    ("request_sent", "request_sent"),
    ("request_settled", "request settled"),
    ("request_processing", "request processing"),

)

CARD_TYPE = (
    ("master", "Mastercard"),
    ("visa", "Visa"),
    ("verve", "Verve"),
    ("amex", "American Express"),
    ("discover", "Discover"),
)

NOTIFICATION_TYPE = (
    ("None", "None"),
    ("Transfer", "Transfer"),
    ("Credit Alert", "Credit Alert"),
    ("Debit Alert", "Debit Alert"),
    ("Sent Payment Request", "Sent Payment Request"),
    ("Recieved Payment Request", "Recieved Payment Request"),
    ("Funded Credit Card", "Funded Credit Card"),
    ("Withdrew Credit Card Funds", "Withdrew Credit Card Funds"),
    ("Deleted Credit Card", "Deleted Credit Card"),
    ("Added Credit Card", "Added Credit Card"),

)

class Deposit(models.Model):
    transaction_id = ShortUUIDField(unique=True, length=15, max_length=20, prefix="DEP")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="depositor")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="deposit_account")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(choices=TRANSACTION_STATUS, max_length=100, default="pending")
    deposit_method = models.CharField(choices=DEPOSIT_METHOD, max_length=50, default="bank_transfer")
    credit_card = models.ForeignKey('CreditCard', on_delete=models.SET_NULL, null=True, blank=True, related_name="deposits")
    date = models.DateTimeField(default=timezone.now)
    
    @property
    def sender(self):
        return None

    @property
    def description(self):
        if self.credit_card:
            return f"Card Deposit (****{self.credit_card.last_four})"
        return "Deposit"

    @property
    def transaction_type(self):
        return "deposit"

    def __str__(self):
        return f"Deposit - {self.transaction_id}"

class Withdrawal(models.Model):
    transaction_id = ShortUUIDField(unique=True, length=15, max_length=20, prefix="WTH")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="withdrawer")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="withdrawal_account")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(choices=TRANSACTION_STATUS, max_length=100, default="pending")
    date = models.DateTimeField(default=timezone.now)

    @property
    def sender(self):
        return self.user

    @property
    def description(self):
        return "Withdrawal"

    @property
    def transaction_type(self):
        return "withdraw"

    def __str__(self):
        return f"Withdrawal - {self.transaction_id}"

class Transfer(models.Model):
    transaction_id = ShortUUIDField(unique=True, length=15, max_length=20, prefix="TRF")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="transfer_sender")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="transfer_source_account")
    
    # Internal Transfer Fields
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="transfer_receiver")
    receiver_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="transfer_destination_account")
    
    # External Transfer Fields
    receiver_name = models.CharField(max_length=100, null=True, blank=True)
    receiver_account_number = models.CharField(max_length=100, null=True, blank=True)
    receiver_bank = models.CharField(max_length=100, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    description = models.CharField(max_length=1000, null=True, blank=True)
    status = models.CharField(choices=TRANSACTION_STATUS, max_length=100, default="pending")
    date = models.DateTimeField(default=timezone.now)

    TRANSFER_TYPES = (
        ("internal", "Internal"),
        ("external", "External"),
    )
    transfer_type = models.CharField(choices=TRANSFER_TYPES, max_length=20, default="internal")

    @property
    def sender(self):
        return self.user

    @property
    def transaction_type(self):
        return "transfer"

    def __str__(self):
        return f"Transfer - {self.transaction_id}"


class PaymentRequest(models.Model):
    transaction_id = ShortUUIDField(unique=True, length=15, max_length=20, prefix="REQ")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_user")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_sender")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_receiver")
    sender_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="request_sender_account")
    receiver_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="request_receiver_account")
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    description = models.CharField(max_length=1000, null=True, blank=True)
    status = models.CharField(choices=TRANSACTION_STATUS, max_length=100, default="pending")
    date = models.DateTimeField(default=timezone.now)

    @property
    def transaction_type(self):
        return "request"

    def __str__(self):
        return f"Payment Request - {self.transaction_id}"


class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_id = ShortUUIDField(unique=True, length=5, max_length=20, prefix="CARD", alphabet="1234567890")

    name = models.CharField(max_length=100)  # Cardholder name
    number = models.CharField(max_length=19)  # Card number (with spaces: 1234 5678 9012 3456)
    month = models.IntegerField()  # Expiry month
    year = models.IntegerField()  # Expiry year (2-digit)
    cvv = models.CharField(max_length=4)  # CVV/CVC

    card_type = models.CharField(choices=CARD_TYPE, max_length=20, default="master")
    card_status = models.BooleanField(default=True)
    
    # Billing Address Fields
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)

    @property
    def last_four(self):
        """Return last 4 digits of card number"""
        digits = ''.join(filter(str.isdigit, str(self.number)))
        return digits[-4:] if len(digits) >= 4 else digits

    @property
    def masked_number(self):
        """Return masked card number like **** **** **** 1234"""
        return f"•••• •••• •••• {self.last_four}"

    @property
    def expiry_display(self):
        """Return formatted expiry like 12/26"""
        return f"{self.month:02d}/{self.year:02d}"

    def __str__(self):
        return f"{self.name} - {self.masked_number}"
    


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notification_type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE, default="none")
    amount = models.IntegerField(default=0)
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    nid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Notification"

    def __str__(self):
        return f"{self.user} - {self.notification_type}"

# Advanced Models moved from advanced_models.py

class Beneficiary(models.Model):
    """Model to store frequently used beneficiaries for quick transfers."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiaries')
    beneficiary_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='beneficiary_of', null=True, blank=True)
    name = models.CharField(max_length=100, help_text="Friendly name for this beneficiary")
    account_number = models.CharField(max_length=100, default="0000000000") # Default for migration, should be required later
    bank_name = models.CharField(max_length=100, default="Paylio")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Beneficiaries"
        ordering = ['-last_used', '-created_at']
        # unique_together constraint removed to allow flexibility
    
    def __str__(self):
        return f"{self.user.username} -> {self.name}"

class AccountFreeze(models.Model):
    """Model to track account freeze/unfreeze history."""
    FREEZE_REASON_CHOICES = (
        ('suspicious_activity', 'Suspicious Activity'),
        ('user_request', 'User Request'),
        ('compliance', 'Compliance Issue'),
        ('security', 'Security Concern'),
        ('other', 'Other'),
    )
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='freeze_history')
    frozen_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=50, choices=FREEZE_REASON_CHOICES)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        status = "Active" if self.is_active else "Resolved"
        return f"Freeze on {self.account.account_number} - {status}"


class ScheduledPayment(models.Model):
    """Model for scheduled/recurring payments."""
    FREQUENCY_CHOICES = (
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    payment_id = ShortUUIDField(unique=True, length=10, max_length=25, prefix="SCHED", alphabet="1234567890")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_payments')
    receiver_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='incoming_scheduled')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=500)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True, help_text="Leave blank for indefinite")
    next_execution = models.DateTimeField()
    last_execution = models.DateTimeField(null=True, blank=True)
    execution_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_execution']
    
    def __str__(self):
        return f"{self.payment_id} - {self.frequency} payment of ${self.amount}"