from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
import uuid
# from charging_station.models import ChargingStation
# from utils.choices import PaymentMode, TransactionStatus

User = get_user_model()

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
    ev_user_balance = models.DecimalField(max_digits=18, decimal_places=2,validators= [MinValueValidator(0)] , default=0)
    station_user_balance = models.DecimalField(max_digits=18, decimal_places=2, validators= [MinValueValidator(0)], default=0)
    
    def __str__(self):
        return f"{self.user}"
    
class Transaction(TimeStampedModel):
    ev_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,blank=True,
                                related_name='ev_user_transaction')
    station_user = models.ForeignKey(User, on_delete=models.CASCADE, 
                                     null=True,blank=True, related_name='station_user_transaction')

    transaction_id = models.UUIDField(
         unique=True,
         default = uuid.uuid4,
         editable = False
         )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    mode_of_payment = models.CharField(choices=PaymentMode, max_length=50)
    transaction_status = models.CharField(choices=TransactionStatus, max_length=50)
    
    def __str__(self):
        return f"{self.transaction_id}"
    
@receiver(post_save, sender=Transaction)
def update_wallet(sender, instance, created, **kwargs):
    if created:
        print(instance.ev_user, instance.station_user)
        end_user_wallet = Wallet.objects.get(user=instance.ev_user)
        station_user_wallet = Wallet.objects.get(user=instance.station_user)
        
        if instance.ev_user != instance.station_user:
            # Deduct amount from end user wallet
            end_user_wallet.ev_user_balance -= instance.amount
            end_user_wallet.save()
            
            # Add amount to owner wallet
            station_user_wallet.station_user_balance += instance.amount
            station_user_wallet.save()
        else:
            # Deduct amount from owner wallet
            station_user_wallet.station_user_balance -= instance.amount
            station_user_wallet.save()
            
    print("A---- ", sender)
    print("B---- ", instance.ev_user != instance.station_user)
    print("C----", created )
    print('D---- ', kwargs)


class Withdraw(TimeStampedModel):
    station_user = models.ForeignKey(User, on_delete=models.CASCADE, 
                                     null=True,blank=True, related_name='withdraw_request')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    note = models.CharField(
        max_length=50,
        null=True,
        blank=True
        )
    
    
    def __str__(self):
        return f"{self.station_user} - {self.amount}"
    
        