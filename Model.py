from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from core.models import SoftDeleteActivatorModel, SoftDeleteTimeStampedModel
from currencies.models import Currency
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from store.models import Store
from user_api_key.models import ModeChoices

from .helpers import process_emi_transaction

User = get_user_model()


class PaymentProvider(SoftDeleteActivatorModel, TimeStampedModel):
    """
    Model representing a payment provider, such as PayPal or Stripe.

    Attributes:
        name (str): The name of the payment provider.
        image (ImageField): An image representing the payment provider.
    """

    name = models.CharField(
        max_length=255, help_text=_("Enter the name of the payment provider.")
    )
    image = models.ImageField(
        upload_to="payment_providers/",
        help_text=_("Select an image to represent the payment provider."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name


class TransactionStatus(TextChoices):
    """
    TextChoices for the status of a PaymentTransaction.

    Attributes:
        AUTHORIZED (str): The transaction has been authorized but not yet captured.
        CAPTURED (str): The transaction has been successfully captured.
        REFUNDED (str): The transaction has been refunded.
        CANCELLED (str): The transaction has been cancelled.
        FAILED (str): The transaction has failed.

    """

    AUTHORIZED = "AUTHORIZED", "Authorized"
    CAPTURED = "CAPTURED", "Captured"
    REFUNDED = "REFUNDED", "Refunded"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED = "FAILED", "Failed"


class EMITransactionStatus(TextChoices):
    """
    ChoiceField for the status of an EMI transaction.

    Attributes:
        ACTIVE (str): The EMI transaction is active.
        COMPLETED (str): The EMI transaction has been completed.
        DUE_PAYMENT (str): The EMI transaction is due for payment.
        REFUNDED (str): The EMI transaction has been refunded.
    """

    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"
    DUE_PAYMENT = "DUE_PAYMENT", "Due Payment"
    REFUNDED = "REFUNDED", "Refunded"


class TransactionType(TextChoices):
    """
    TextChoices for the type of a Transaction.

    Attributes:
        WITHDRAW (str): 'withdraw', "A withdrawal transaction."
        DEPOSIT (str): 'deposit', "A deposit transaction."
        REFUND (str): 'refund', "A refund transaction."
        PURCHASE (str): 'purchase', "A purchase transaction."
        INSTALLMENT (str): 'installment', "An installment transaction."
        BNPL_CREDIT (str): 'bnpl_credit', "A BNPL credit transaction."
        BNPL_COMMISION (str): 'bnpl_commission', "A BNPL commission transaction."
    """

    WITHDRAW = "withdraw", "Withdrawn"
    DEPOSIT = "deposit", "Deposit"
    REFUND = "refund", "Refund"
    PURCHASE = "purchase", "Purchase"
    INSTALLMENT = "installment", "Installment"
    BNPL_CREDIT = "bnpl_credit", "BNPL Credit"
    BNPL_COMMISION = "bnpl_commission", "BNPL Commission"
    CASHBACK = "cashback", "Cashback"


class PaymentTransaction(SoftDeleteTimeStampedModel):
    """
    Model representing a payment transaction made by a user.

    Fields:
        amount: The amount of the transaction.
        payment_token: The token associated with the payment.
        provider: The payment provider used to process the transaction.
        status: The status of the transaction, e.g. "Succeeded", "failed", "pending".
        store: The store associate with transation.
        currency: The currency used for the transaction.
        metadata: Additional metadata associated with the transaction.
        user: The user who made the transaction.
    """

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text=_("The amount of the transaction.")
    )
    payment_token = models.CharField(
        max_length=255, help_text=_("The token associated with the payment.")
    )
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.CASCADE,
        help_text=_("The payment provider used to process the transaction."),
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        help_text=_("Select the store associated with this payment provider."),
    )
    status = models.CharField(
        choices=TransactionStatus.choices,
        default=TransactionStatus.AUTHORIZED,
        max_length=20,
        help_text=_("The status of the transaction."),
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        help_text=_("The currency used for the transaction."),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata associated with the transaction."),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
        help_text=_("The user who made the transaction."),
    )

    def __str__(self):
        return self.payment_token

    class Meta:
        verbose_name_plural = _("Payment Transactions")
        verbose_name = _("Payment Transaction")

    @property
    def get_order_receipt_id(self):
        order_receipt = self.metadata.get("order_receipt")
        if order_receipt:
            return order_receipt.split("_")[-1]
        return None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the user's wallet balance if the payment was captured or refunded
        if self.status in [TransactionStatus.CAPTURED, TransactionStatus.REFUNDED]:
            transactions = Transaction.objects.filter(payment_transaction=self)
            for transaction in transactions:
                wallet = transaction.user.wallet
                wallet.balance += transaction.amount
                wallet.save(update_fields=["balance"])


class EMI(SoftDeleteTimeStampedModel):
    """
    Model representing an Equated Monthly Installment (EMI) payment.

    Fields:
        amount: The amount of the EMI payment.
        payment_transaction: The payment transaction associated with this EMI payment.
        installment_number: The number of the EMI installment.
        emi_schedule_date: The date and time when the EMI payment was made.
        penalty: The penalty associated with the EMI payment.
    """

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text=_("The amount of the EMI payment.")
    )
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        related_name="emis",
        on_delete=models.CASCADE,
        help_text=_("The payment transaction associated with this EMI payment."),
    )
    installment_number = models.PositiveSmallIntegerField(
        help_text=_("The number of the EMI installment.")
    )
    emi_schedule_date = models.DateTimeField(
        default=datetime.now,
        help_text=_("The date and time when the EMI payment was made."),
    )
    emi_payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("The date and time when the Actual EMI payment was made."),
    )
    status = models.CharField(
        choices=EMITransactionStatus.choices,
        default=EMITransactionStatus.ACTIVE,
        max_length=20,
        help_text=_("The status of the EMI transaction."),
    )
    penalty = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        null=True,
        blank=True,
        default=0.0,
        help_text=_("The penalty associated with the EMI payment."),
    )
    penalty_days = models.PositiveSmallIntegerField(
        default=0,
        help_text=_(
            "The number of days after which a penalty will be applied to this EMI payment.\
            set the max number of days from the rules"
        ),
    )


class Transaction(SoftDeleteTimeStampedModel):
    """
    Model representing a transaction made by a user.

    Fields:
        amount: The amount of the transaction.
        payment_transaction: The payment transaction associated with this transaction.
        type: The type of transaction, e.g. "Withdrawn", "Deposit", "Refund", "Installment",
        "BNPL Credit." "BNPL Commission"
        user: The user who made the transaction.
    """

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text=_("The amount of the transaction.")
    )
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        related_name="transactions",
        null=True,
        on_delete=models.CASCADE,
        help_text=_("The payment transaction associated with this transaction."),
    )
    type = models.CharField(
        choices=TransactionType.choices,
        max_length=20,
        help_text=_("The type of transaction."),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text=_("The user who made the transaction."),
    )
    emi = models.ForeignKey(
        EMI,
        on_delete=models.CASCADE,
        null=True,
        help_text=_("The EMI Transaction for which the penalty is calculated."),
    )

    class Meta:
        verbose_name_plural = _("Transactions")
        verbose_name = _("Transaction")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the user's wallet balance if the payment was captured or refunded
        if (
            self
            and self.payment_transaction
            and self.payment_transaction.status
            in [TransactionStatus.CAPTURED, TransactionStatus.REFUNDED]
        ):
            self.update_wallet_balance(self.amount)
        elif self.type == TransactionType.DEPOSIT:
            self.update_wallet_balance(self.amount)
            process_emi_transaction(
                current_date=date.today(), status=EMITransactionStatus.DUE_PAYMENT
            )

    def update_wallet_balance(self, amount: Decimal) -> None:
        """
        Updates the wallet balance of the user associated with this transaction.
        """
        wallet = self.user.wallet
        wallet.balance += amount
        wallet.save(update_fields=["balance"])
        if (
            self
            and self.payment_transaction
            and self.payment_transaction.status
            in [TransactionStatus.CAPTURED, TransactionStatus.REFUNDED]
        ):
            wallet = self.user.wallet
            wallet.balance += self.amount
            wallet.save(update_fields=["balance"])


class WithdrawRequestStatus(models.TextChoices):
    """Valid choices for withdraw request status"""

    IN_REVIEW = "in_review", _("In Review")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")
    TRANSFERRED = "transferred", _("Transferred")


class WithdrawRequest(SoftDeleteTimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="withdraw_requests",
        help_text=_("The user who made the withdraw request."),
    )
    act_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="processed_requests",
        help_text=_("The user who approved/rejected the withdraw request."),
    )
    status = models.CharField(
        choices=WithdrawRequestStatus.choices,
        default=WithdrawRequestStatus.IN_REVIEW,
        max_length=20,
        help_text=_("The status of the withdraw request."),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_("The amount of the withdraw request."),
    )


class EMIRules(SoftDeleteTimeStampedModel):
    """
    Model representing the EMI rules for a payment transaction.

    Attributes:
        min_amount (Decimal): The minimum amount for an EMI payment.
        max_amount (Decimal): The maximum amount for an EMI payment.
        max_installments (int): The maximum number of installments allowed
        for an EMI payment.
        first_installment_percentage (Decimal): The percentage of the total
        amount to be paid as the first installment.
    """

    min_amount = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        help_text=_("The minimum amount for an EMI payment."),
    )
    max_amount = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        help_text=_("The maximum amount for an EMI payment."),
    )
    max_installments = models.PositiveSmallIntegerField(
        default=1,
        help_text=_("The maximum number of installments allowed for an EMI payment."),
    )
    first_installment_percentage = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text=_(
            "The percentage of the total amount to be paid as the first installment."
        ),
    )

    class Meta:
        verbose_name = "EMI Rule"
        verbose_name_plural = "EMI Rules"

    def __str__(self):
        return f"{self.max_installments} Installments for {self.max_amount}"


class EMIPenaltyRule(SoftDeleteTimeStampedModel):
    """
    Model representing the penalty rules for an EMI payment.

    Attributes:
        amount (Decimal): The penalty amount.
        start_period (int): The start of the period for which the penalty is applicable.
        end_period (int): The end of the period for which the penalty is applicable.
    """

    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text=_("The penalty amount.")
    )
    start_period = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("The start of the period for which the penalty is applicable."),
    )
    end_period = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("The end of the period for which the penalty is applicable."),
    )

    class Meta:
        verbose_name = "EMI Penalty Rule"
        verbose_name_plural = "EMI Penalty Rules"

    @staticmethod
    def get_penalty_rule(days_late: int) -> Optional["EMIPenaltyRule"]:
        """
        Get the penalty rule for a given number of days late.

        Args:
            days_late (int): The number of days late for the EMI payment.

        Returns:
            EMIPenaltyRule: The penalty rule for the given number of days late or
            None if no rule is found.
        """
        penalty_rules = EMIPenaltyRule.objects.filter(
            start_period__lte=days_late, end_period__gte=days_late
        ).order_by("end_period")
        return penalty_rules.first()

    def calculate_penalty_amount(self, emi_amount: Decimal) -> Decimal:
        """
        Calculate the penalty amount for the given EMI amount based on the penalty rule.

        Args:
            emi_amount (Decimal): The EMI amount.

        Returns:
            Decimal: The penalty amount.
        """
        return round(emi_amount * (self.amount / 100), 2)


class EMIPenaltyCalculation(SoftDeleteTimeStampedModel):
    """
    Model representing the penalty calculation details for an EMI payment.

    Attributes:
        emi (EMI): The EMI payment for which the penalty is calculated.
        amount (Decimal): The penalty amount.
        emi_penalty_rule (EMIPenaltyRule): The penalty rule applied for the EMI payment.
        penalty_calculation_details (dict): A dictionary containing details of the
        penalty calculation.
    """

    emi = models.ForeignKey(
        EMI,
        on_delete=models.CASCADE,
        help_text=_("The EMI payment for which the penalty is calculated."),
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text=_("The penalty amount.")
    )
    emi_penalty_rule = models.ForeignKey(
        EMIPenaltyRule,
        on_delete=models.CASCADE,
        help_text=_("The penalty rule applied for the EMI payment."),
    )
    penalty_calculation_details = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("A dictionary containing details of the penalty calculation."),
    )

    class Meta:
        verbose_name = "EMI Penalty Calculation"
        verbose_name_plural = "EMI Penalty Calculations"


class Event(SoftDeleteActivatorModel, TimeStampedModel):
    """
    Model to store events that can trigger webhooks.

    Attributes:
        name (str) :The name of the event.
        parent_event (Event, optional ): The parent event of the event, if any.
    """

    name = models.CharField(max_length=50)
    parent_event = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.name


class WebhookStatus(TextChoices):
    """
    Choices for the status of a webhook.
    Attributes:
        ENABLED (str): "enabled", "Enabled"
        DISABLED (str): "disabled", "Disabled"
    """

    ENABLED = "enabled", "Enabled"
    DISABLED = "disabled", "Disabled"


class Webhook(SoftDeleteActivatorModel, TimeStampedModel):
    """
    Model to store webhooks.

    Attributes:
        mode (str): The mode of the webhook, either 'live' or 'test'.
        webhook_url (str): The URL where the webhook will be sent.
        secret_key (str): The secret key for the webhook, defaults to None.
        status (str): The status of the webhook, either 'enabled' or 'disabled'.
        events (Event): The events that trigger the webhook.
    """

    mode = models.CharField(
        max_length=4, choices=ModeChoices.choices, help_text="Mode of the webhook"
    )
    webhook_url = models.URLField(
        max_length=200, help_text="URL where the webhook will be sent"
    )
    secret_key = models.CharField(
        max_length=50, blank=True, null=True, help_text="Secret key for the webhook"
    )
    status = models.CharField(
        max_length=20,
        choices=WebhookStatus.choices,
        default=WebhookStatus.ENABLED,
        help_text="Whether the webhook is enabled or disabled",
    )
    events = models.ManyToManyField(Event, help_text="Events that trigger the webhook")

    def __str__(self):
        return self.webhook_url


class WebhookPayload(SoftDeleteActivatorModel, TimeStampedModel):
    """
    Model to store payloads sent with webhooks.

    Attributes:
        webhook (Webhook): The webhook that the payload belongs to.
        payload (JSON): The JSON payload sent with the webhook.
    """

    webhook = models.ForeignKey(
        Webhook,
        on_delete=models.CASCADE,
        help_text="Webhook that the payload belongs to",
    )
    payload = models.JSONField(help_text="JSON payload sent with the webhook")

    def __str__(self):
        return f"{self.webhook} Payload"
