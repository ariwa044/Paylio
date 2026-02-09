from django.urls import path
from .views import index, about_us, terms_of_service, privacy_policy, contact_us
from .transfer import search_using_account, AmountTranfare, AmountTranfareProcess,TransactionConfirmation,TransfarProcess, TransfarCompleted, transfer_selection, search_external_account, TransfarPending
from .transaction import transaction_list, transaction_detail
from .payment_request import SearchUserRequest, AmountRequest, AmountRequestProcess, RequestConfirmation, RequestCompleted, RequestFinialProcess, settlement_confirmation, settlement_processing, SettlementCompleted, delete_payment_request
from .credit_card import credit_card_detail, all_cards, add_card, delete_card
from .deposit import (
    initiate_deposit, confirm_deposit, process_deposit,
    deposit_success, deposit_failure, bank_transfer_deposit,
    card_deposit, deposit_with_saved_card,  # crypto_deposit  # Commented out - disabled features
)
from .withdrawal import (
    initiate_withdrawal, confirm_withdrawal, process_withdrawal,
    withdrawal_pending, withdrawal_success, withdrawal_failure
)
from .notification_views import (
    notification_list, mark_notification_read, mark_all_notifications_read,
    get_unread_notifications, delete_notification
)
app_name = 'core'

urlpatterns = [
    path("", index, name='index'),
    
    # Static Pages
    path('about-us/', about_us, name='about-us'),
    path('terms-of-service/', terms_of_service, name='terms-of-service'),
    path('privacy-policy/', privacy_policy, name='privacy-policy'),
    path('contact-us/', contact_us, name='contact-us'),
    
    # Deposit URLs
    path('deposit/', initiate_deposit, name='initiate-deposit'),
    path('deposit/bank-transfer/', bank_transfer_deposit, name='bank-transfer-deposit'),
    path('deposit/card/', card_deposit, name='card-deposit'),
    path('deposit/saved-card/<str:card_id>/', deposit_with_saved_card, name='deposit-with-saved-card'),
    # path('deposit/crypto/', crypto_deposit, name='crypto-deposit'),  # Disabled - no integration
    path('deposit/confirm/<str:transaction_id>/', confirm_deposit, name='confirm-deposit'),
    path('deposit/process/<str:transaction_id>/', process_deposit, name='process-deposit'),
    path('deposit/success/<str:transaction_id>/', deposit_success, name='deposit-success'),
    path('deposit/failed/<str:transaction_id>/', deposit_failure, name='deposit-failure'),
    
    # Withdrawal URLs
    # path('withdrawal/', initiate_withdrawal, name='initiate-withdrawal'),
    # path('withdrawal/confirm/<str:transaction_id>/', confirm_withdrawal, name='confirm-withdrawal'),
    # path('withdrawal/process/<str:transaction_id>/', process_withdrawal, name='process-withdrawal'),
    # path('withdrawal/pending/<str:transaction_id>/', withdrawal_pending, name='withdrawal-pending'),
    # path('withdrawal/success/<str:transaction_id>/', withdrawal_success, name='withdrawal-success'),
    # path('withdrawal/failure/<str:transaction_id>/', withdrawal_failure, name='withdrawal-failure'),
    
    path('selection/', transfer_selection, name='transfer-selection'),
    path('search-external-account/', search_external_account, name='search-external-account'),
    path('search-account/', search_using_account, name='search-account'),
    path('amount-transfare/<account_number>/',AmountTranfare , name='amount-transfare'),
    path('amount-transfare-process/<account_number>/',AmountTranfareProcess , name='amount-transfare-Process'),
    path('transfare-confirm/<account_number>/<transaction_id>/',TransactionConfirmation , name='transfare-confirmation'),
    path('transfare-process/<account_number>/<transaction_id>/',TransfarProcess , name='transaction-process'),
    path('transfare-completed/<account_number>/<transaction_id>/',TransfarCompleted , name='transfar-completed'),
    path('transfare-pending/<account_number>/<transaction_id>/',TransfarPending , name='transfare-pending'),



    #transaction



    path('transaction/',transaction_list, name='transaction-list' ),
    path('transaction/<transaction_id>/',transaction_detail, name='transaction-detail' ),

    #payment_request

    path('request-search-user/',SearchUserRequest, name='request-search-user' ),
    path('amount-request/<account_number>',AmountRequest, name='amount-request' ),
    path('amount-request-process/<account_number>/',AmountRequestProcess , name='amount-request-Process'),
    path('request-confirm/<account_number>/<transaction_id>/',RequestConfirmation , name='request-confirmation'),
    path('request-process/<account_number>/<transaction_id>/',RequestFinialProcess , name='request-finial-process'),
    path('request-completed/<account_number>/<transaction_id>/',RequestCompleted , name='request-completed'),
    path('settlement-confirmation/<account_number>/<transaction_id>/', settlement_confirmation, name='settlement-confirmation'),
    path('settlement-processing/<account_number>/<transaction_id>/',settlement_processing, name= 'settlement_processing'),
    path('settlement-completed/<account_number>/<transaction_id>/',SettlementCompleted , name='settlement-completed'),
    path('delete-request/<account_number>/<transaction_id>/',delete_payment_request , name='delete-request'),

    # Credit Cards
    path('cards/', all_cards, name="all-cards"),
    path('cards/add/', add_card, name="add-card"),
    path('card/<card_id>/', credit_card_detail, name="card_detail"),
    path('card/delete/<card_id>/', delete_card, name="delete-card"),

    # Notifications

    path('notifications/mark-read/<str:nid>/', mark_notification_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark-all-notifications-read'),
    path('notifications/unread/', get_unread_notifications, name='get-unread-notifications'),
    path('notifications/delete/<str:nid>/', delete_notification, name='delete-notification'),




]
