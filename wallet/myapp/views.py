from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView
from .models import Wallet, Transaction
from .api.serializers import WalletSerializer, WalletTransaction
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from utils.choices import PaymentStatus, PaymentType, PaymentMode

User = get_user_model()


class WalletDetailAPIView(ListAPIView):
    
    def get(self, request):
        user = request.user
        queryset = Wallet.objects.filter(user=user).first()
        serializer_class = WalletSerializer(queryset)
        return Response(serializer_class.data)
    

class WalletTransactionView(ListAPIView):
    
    def get(self, request):
        self.user = request.user
        if self.user.groups.filter(name = "ev owner").exists():
            self.queryset = Transaction.objects.filter(ev_user=self.user)
        elif self.user.groups.filter(name = "station owner").exists():
            self.queryset = Transaction.objects.filter(station_user=self.user)
        serializer_class = WalletTransaction(self.queryset, many=True)
        return Response(serializer_class.data)
        # def get(self, request):
        #     wallet = Wallet.objects.get(user=request.user)
        #     serializer_class = WalletTransaction
        #     print(serializer_class.data)
        #     return Response(serializer_class.data)
        
            
        #     return wallet
        # except Wallet.DoesNotExist:
        #     return Response({'error': 'Wallet does not exist'}, status=status.HTTP_404_NOT_FOUND)

    # def post(self, request, wallet_id):
    #     wallet = self.get_wallet(wallet_id)
    #     if not wallet:
    #         return Response({'error': 'Wallet does not exist'}, status=status.HTTP_404_NOT_FOUND)

    #     serializer = WalletTransactionForEvOwnerSerializer(data=request.data)
    #     if serializer.is_valid():
    #         amount = serializer.validated_data['amount']
    #         if wallet.balance + amount < 0:
    #             return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

    #         transaction = serializer.save()
    #         wallet.balance += amount
    #         wallet.save()

    #         return Response({'transaction_id': transaction.id}, status=status.HTTP_201_CREATED)
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @login_required
# def transaction_view(request):
#     if request.method == 'POST':
#         wallet = get_object_or_404(Wallet, user=request.user)
#         # Get transaction details from the request data
#         amount = request.POST.get('amount')
#         transaction_type = request.POST.get('transaction_type')
#         # Perform necessary validation on the amount and transaction type
#         if transaction_type == 'credit':
#             wallet.balance += amount
#         elif transaction_type == 'debit':
#             if amount > wallet.balance:
#                 return render(request, 'transaction_failure.html', {'error': 'Insufficient balance'})
#             wallet.balance -= amount
#         else:
#             return render(request, 'transaction_failure.html', {'error': 'Invalid transaction type'})
#         # Create a new transaction
#         transaction = Transaction.objects.create(wallet=wallet, amount=amount, transaction_type=transaction_type)
#         wallet.save()
#         return render(request, 'transaction_success.html', {'transaction': transaction})
#     return render(request, 'transaction_form.html')
