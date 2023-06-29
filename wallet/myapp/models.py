from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth.models import User
# from charging_station.models import ChargingStation
# Create your models here.

PaymentMode =(
    ("wallet", "Wallet"),
    ("upi", "Upi"),
    ("card", "Card")
)

TransactionStatus=(
    ("paid", "Paid"),
    ("refunded", "Refunded"),
    ("canceled", "Canceled"),
    ("failed", "Failed"),
)

class Wallet(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.user}"
    
class TransactionForEvOwner(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,blank=True)
    transaction_id = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    # charging_station = models.ForeignKey(ChargingStaion, on_delete=models.CASCADE)
    mode_of_payment = models.CharField(choices=PaymentMode, max_length=50)
    transaction_status = models.CharField(choices=TransactionStatus, max_length=50)
    
    def __str__(self):
        return self.transaction_id
    


    