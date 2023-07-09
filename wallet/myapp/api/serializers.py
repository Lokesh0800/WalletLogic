from rest_framework import serializers
from ..models import Wallet, Transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'ev_user_balance', 'station_user_balance')
    def to_representation(self, instance):
        if User.objects.filter(id=instance.id, groups__name__in=['ev owner']):
            self.fields.pop('statio n_user_balance')
        elif User.objects.filter(id=instance.id, groups__name__in=['station owner']):
            self.fields.pop('ev_user_balance')
        return super().to_representation(instance)
    
    
class WalletTransaction(serializers.ModelSerializer):
    class Meta:
        model = Transaction 
        fields = ('ev_user', 'station_user','created','amount', 'mode_of_payment', 'payment_status')
    
    def to_representation(self, instance):
        self.user = instance.ev_user or instance.station_user
        if self.user.groups.filter(name = "ev owner").exists():
            print("@@@@@@@@@@@@@@@")
            self.fields.pop('station_user')
        elif self.user.groups.filter(name = "ev owner").exists():
            self.fields.pop('ev_user')
        print("**********************")
        
        return super().to_representation(instance)    
    # def to_representation(self, instance):
        
    #     return super().to_representation(instance)
