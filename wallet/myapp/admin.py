from django.contrib import admin
# from utils.utils import get_model
from .models import *
# Register your models here.

# Wallet = get_model('wallet', 'Wallet')
# Transaction = get_model('wallet', 'Transaction')

admin.site.register(Wallet)
admin.site.register(Transaction)
