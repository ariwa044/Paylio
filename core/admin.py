from django.contrib import admin
from .models import Transfer, Deposit, Withdrawal, PaymentRequest, CreditCard, Notification, Beneficiary, AccountFreeze, ScheduledPayment
# Register your models here.

class TransferAdmin(admin.ModelAdmin):
    list_editable = ['amount', 'status']
    list_display = ['user', 'amount', 'status', 'transfer_type', 'receiver', 'date']

class DepositAdmin(admin.ModelAdmin):
    list_editable = ['amount', 'status']
    list_display = ['user', 'amount', 'status', 'date']

class WithdrawalAdmin(admin.ModelAdmin):
    list_editable = ['amount', 'status']
    list_display = ['user', 'amount', 'status', 'date']

class PaymentRequestAdmin(admin.ModelAdmin):
    list_editable = ['amount', 'status']
    list_display = ['user', 'amount', 'status', 'sender', 'receiver', 'date']

class CreditCardAdmin(admin.ModelAdmin):
    list_editable = ['card_type', 'card_status']
    list_display = ['user', 'name', 'card_type', 'card_status', 'date']    

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'amount' ,'date']

class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'account_number', 'bank_name', 'is_active']

class AccountFreezeAdmin(admin.ModelAdmin):
    list_display = ['account', 'frozen_at', 'reason', 'is_active']
    list_filter = ['is_active', 'reason', 'frozen_at']

class ScheduledPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'amount', 'frequency', 'status', 'next_execution']
    list_filter = ['status', 'frequency']

admin.site.register(Transfer, TransferAdmin)
admin.site.register(Deposit, DepositAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)
admin.site.register(PaymentRequest, PaymentRequestAdmin)
admin.site.register(CreditCard, CreditCardAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Beneficiary, BeneficiaryAdmin)
admin.site.register(AccountFreeze, AccountFreezeAdmin)
admin.site.register(ScheduledPayment, ScheduledPaymentAdmin)

