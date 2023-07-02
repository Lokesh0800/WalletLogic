from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from rest_framework import generics
from .models import Wallet, Transaction
from .serializers import WalletSerializer, WalletTransactionForEvOwnerSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class WalletDetailAPIView(generics.RetrieveAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

class TransactionCreateAPIView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = WalletTransactionForEvOwnerSerializer


# class WalletTransactionView(APIView):
#     def get_wallet(self, wallet_id):
#         try:
#             wallet = Wallet.objects.get(id=wallet_id)
#             return wallet
#         except Wallet.DoesNotExist:
#             return None

#     def post(self, request, wallet_id):
#         wallet = self.get_wallet(wallet_id)
#         if not wallet:
#             return Response({'error': 'Wallet does not exist'}, status=status.HTTP_404_NOT_FOUND)

#         serializer = WalletTransactionForEvOwnerSerializer(data=request.data)
#         if serializer.is_valid():
#             amount = serializer.validated_data['amount']
#             if wallet.balance + amount < 0:
#                 return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

#             transaction = serializer.save()
#             wallet.balance += amount
#             wallet.save()

#             return Response({'transaction_id': transaction.id}, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
