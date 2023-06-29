from django.urls import path
from .views import WalletDetailAPIView, TransactionCreateAPIView
from .views import WalletTransactionView

urlpatterns = [
    path('wallet/<int:pk>/', WalletDetailAPIView.as_view(), name='wallet-detail'),
    path('transaction/create/', TransactionCreateAPIView.as_view(), name='transaction-create'),
    path('wallet/<int:wallet_id>/transaction/', WalletTransactionView.as_view(), name='wallet-transaction'),

]

