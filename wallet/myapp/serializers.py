from rest_framework import serializers
from .models import Wallet, Transaction

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'balance')

class WalletTransactionForEvOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction 
        fields = ('ev_user', 'station_user','created','amount', 'mode_of_payment', 'transaction_status')
