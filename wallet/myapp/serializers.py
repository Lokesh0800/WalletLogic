from rest_framework import serializers
from .models import Wallet, TransactionForEvOwner

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'balance')

class WalletTransactionForEvOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionForEvOwner
        fields = ('user','created', 'transaction_id', 'amount', 'mode_of_payment', 'transaction_status')
