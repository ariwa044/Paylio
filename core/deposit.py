from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
# from nowpayments import NOWPayments  # Commented out - incomplete integration
from account.models import Account
from .models import (
    Deposit, Notification, CreditCard,
    # CRYPTO_CURRENCIES,  # Commented out - crypto feature disabled
    DEPOSIT_METHOD
)
# from .crypto_service import CryptoExchangeService  # Commented out - module doesn't exist
from .utils import is_account_frozen, get_freeze_reason_display, send_html_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from userauths.models import User

# Initialize NOWPayments client - COMMENTED OUT
# nowpayments_client = NOWPayments(settings.NOWPAYMENTS_API_KEY)
# if settings.NOWPAYMENTS_SANDBOX:
#     nowpayments_client.set_sandbox()

@login_required
def initiate_deposit(request):
    """View to display deposit method selection - Bank Transfer Only."""
    try:
        account = Account.objects.get(user=request.user)
        if not account.kyc_confirmed:
            messages.warning(request, "Please complete your KYC verification first.")
            return redirect("account:kyc-reg")
        
        # Check if account is frozen
        is_frozen, freeze_record = is_account_frozen(account)
        if is_frozen:
            messages.error(request, f"Your account is frozen: {get_freeze_reason_display(freeze_record)}. Deposits are not allowed.")
            return redirect("account:account")
            
        # SIMPLIFIED: Only bank transfer deposits supported
        # Crypto and card deposits commented out until properly implemented
        credit_cards = CreditCard.objects.filter(user=request.user, card_status=True).order_by('-date')
        
        return render(request, "core/deposit/select_method.html", {
            "account": account,
            "credit_cards": credit_cards,
        })
            
    except Account.DoesNotExist:
        messages.error(request, "No account found.")
        return redirect("account:dashboard")

@login_required
def confirm_deposit(request, transaction_id):
    """View to confirm deposit details before processing."""
    transaction = get_object_or_404(Deposit, 
                                  transaction_id=transaction_id,
                                  user=request.user)
    
    if transaction.status != "pending":
        messages.warning(request, "This deposit has already been processed.")
        return redirect("core:transaction-detail", transaction_id=transaction_id)
    
    if request.method == "POST":
        return redirect("core:process-deposit", transaction_id=transaction_id)
    
    return render(request, "core/deposit/confirm_deposit.html", {
        "transaction": transaction
    })

@login_required
@transaction.atomic
def process_deposit(request, transaction_id):
    """Process the deposit transaction."""
    txn = get_object_or_404(Deposit, 
                           transaction_id=transaction_id,
                           user=request.user)
    
    if txn.status != "pending":
        messages.warning(request, "This deposit has already been processed.")
        return redirect("core:transaction-detail", transaction_id=transaction_id)
    
    try:
        account = Account.objects.get(user=request.user)
        
        # Update transaction status to processing (pending admin approval)
        txn.status = "processing"
        txn.save()
        
        # NOTE: Balance update is now handled by signal when Admin approves (sets to completed)
        
        # Create notification for request
        Notification.objects.create(
            user=request.user,
            notification_type="Deposit Request", # Or similar, generic 'None' or new type. 
        )
        
        # Email Admins
        try:
            subject = f'New Deposit Request: ${txn.amount}'
            message = f'User {txn.user.username} (Account: {account.account_number}) has requested a deposit of ${txn.amount}.\nTransaction ID: {txn.transaction_id}\n\nPlease review and approve.'
            context = {
                'subject_header': 'New Deposit Request',
                'message': message
            }
            admins = User.objects.filter(is_superuser=True)
            recipient_list = [admin.email for admin in admins]
            send_html_email(subject, recipient_list, context)
        except:
            pass
        
        # Email User
        try:
            user_subject = f'Deposit Request Received: ${txn.amount}'
            user_message = f'Hello {txn.user.username},\n\nWe have received your deposit request of ${txn.amount}.\nTransaction ID: {txn.transaction_id}\n\nYour request is currently being processed and will be screened shortly. Once approved, the funds will be credited to your account immediately.\n\nThank you for banking with us.'
            user_context = {
                'subject_header': 'Deposit Processing',
                'message': user_message
            }
            send_html_email(user_subject, [txn.user.email], user_context)
        except:
            pass
        
        messages.success(request, f"Deposit request of {txn.amount} submitted successfully. Pending approval.")
        return redirect("core:deposit-success", transaction_id=transaction_id)
        
    except Account.DoesNotExist:
        txn.status = "failed"
        txn.save()
        messages.error(request, "Account not found.")
        return redirect("account:dashboard")
    except Exception as e:
        txn.status = "failed"
        txn.save()
        messages.error(request, f"Error processing deposit: {str(e)}")
        return redirect("core:deposit-failure", transaction_id=transaction_id)

@login_required
def deposit_success(request, transaction_id):
    """Display successful deposit completion page."""
    transaction = get_object_or_404(Deposit, 
                                  transaction_id=transaction_id,
                                  user=request.user)
    
    return render(request, "core/deposit/deposit_success.html", {
        "transaction": transaction
    })

@login_required
def deposit_failure(request, transaction_id):
    """Display deposit failure page with reason."""
    transaction = get_object_or_404(Deposit, 
                                  transaction_id=transaction_id,
                                  user=request.user,
                                  status="failed")
    
    return render(request, "core/deposit/deposit_failure.html", {
        "transaction": transaction
    })

@login_required
def bank_transfer_deposit(request):
    """Handle bank transfer deposit method."""
    try:
        account = Account.objects.get(user=request.user)
        if not account.kyc_confirmed:
            messages.warning(request, "Please complete your KYC verification first.")
            return redirect("account:kyc-reg")
            
        if request.method == "POST":
            amount = request.POST.get("amount")
            reference = request.POST.get("reference")
            
            if not amount or not reference:
                messages.error(request, "Please provide both amount and payment reference")
                return redirect("core:bank-transfer-deposit")
                
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValidationError("Amount must be greater than zero")
                    
                # Create pending transaction
                transaction = Deposit.objects.create(
                    user=request.user,
                    amount=amount,
                    status="pending",
                    # description=f"Bank transfer deposit (Ref: {reference})",
                    account=account
                )
                
                return redirect("core:confirm-deposit", transaction_id=transaction.transaction_id)
                
            except (ValueError, ValidationError) as e:
                messages.error(request, str(e))
                return redirect("core:bank-transfer-deposit")
                
        return render(request, "core/deposit/bank_transfer.html", {
            "account": account
        })
        
    except Account.DoesNotExist:
        messages.error(request, "No account found.")
        return redirect("account:dashboard")

@login_required
def card_deposit(request):
    """Handle adding a new card for deposit."""
    try:
        account = Account.objects.get(user=request.user)
        if not account.kyc_confirmed:
            messages.warning(request, "Please complete your KYC verification first.")
            return redirect("account:kyc-reg")
            
        if request.method == "POST":
            # amount = request.POST.get("amount") # Removed amount
            name = request.POST.get("card_holder")
            number = request.POST.get("card_number")
            month = request.POST.get("expiry_month")
            year = request.POST.get("expiry_year")
            cvv = request.POST.get("cvv")
            card_type = request.POST.get("card_type")
            
            # Billing Address
            address_line1 = request.POST.get("address_line1")
            address_line2 = request.POST.get("address_line2")
            city = request.POST.get("city")
            state = request.POST.get("state")
            zip_code = request.POST.get("zip_code")
            country = request.POST.get("country")
            
            # Validate inputs
            if not all([name, number, month, year, cvv, card_type,
                       address_line1, city, state, zip_code, country]):
                messages.error(request, "Please fill in all required fields")
                return redirect("core:card-deposit")
                
            try:
                # Basic validation
                month_int = int(month)
                year_int = int(year)
                if month_int < 1 or month_int > 12:
                    raise ValueError("Invalid month")
                    
                # Create the card
                card = CreditCard.objects.create(
                    user=request.user,
                    name=name,
                    number=number,
                    month=month_int,
                    year=year_int,
                    cvv=cvv,
                    card_type=card_type,
                    address_line1=address_line1,
                    address_line2=address_line2,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    country=country,
                )
                
                Notification.objects.create(
                    user=request.user,
                    notification_type="Added Credit Card"
                )
                
                messages.success(request, "Card added successfully! Now enter deposit amount.")
                return redirect("core:deposit-with-saved-card", card_id=card.card_id)
                
            except (ValueError, ValidationError) as e:
                messages.error(request, str(e))
                return redirect("core:card-deposit")
                
        return render(request, "core/deposit/card_payment.html", {
            "account": account
        })
        
    except Account.DoesNotExist:
        messages.error(request, "No account found.")
        return redirect("account:dashboard")


@login_required
def deposit_with_saved_card(request, card_id):
    """Handle deposit using a saved card."""
    try:
        account = Account.objects.get(user=request.user)
        credit_card = CreditCard.objects.get(card_id=card_id, user=request.user)
        
        if not account.kyc_confirmed:
            messages.warning(request, "Please complete your KYC verification first.")
            return redirect("account:kyc-reg")
        
        # Check if account is frozen
        is_frozen, freeze_record = is_account_frozen(account)
        if is_frozen:
            messages.error(request, f"Your account is frozen: {get_freeze_reason_display(freeze_record)}.")
            return redirect("account:account")
            
        if request.method == "POST":
            amount = request.POST.get("amount")
            
            if not amount:
                messages.error(request, "Please enter an amount")
                return redirect("core:deposit-with-saved-card", card_id=card_id)
                
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValidationError("Amount must be greater than zero")
                    
                # Create pending transaction linked to saved card
                deposit = Deposit.objects.create(
                    user=request.user,
                    amount=amount,
                    status="pending",
                    deposit_method="saved_card",
                    credit_card=credit_card,
                    account=account
                )
                
                return redirect("core:confirm-deposit", transaction_id=deposit.transaction_id)
                
            except (ValueError, ValidationError) as e:
                messages.error(request, str(e))
                return redirect("core:deposit-with-saved-card", card_id=card_id)
                
        return render(request, "core/deposit/deposit_with_card.html", {
            "account": account,
            "credit_card": credit_card,
        })
        
    except Account.DoesNotExist:
        messages.error(request, "No account found.")
        return redirect("account:dashboard")
    except CreditCard.DoesNotExist:
        messages.error(request, "Card not found.")
        return redirect("core:all-cards")

@login_required
def crypto_deposit(request):
    """Handle cryptocurrency deposit method."""
    try:
        account = Account.objects.get(user=request.user)
        if not account.kyc_confirmed:
            messages.warning(request, "Please complete your KYC verification first.")
            return redirect("account:kyc-reg")
            
        if request.method == "POST":
            amount = request.POST.get("amount")
            crypto_currency = request.POST.get("crypto_currency")
            
            if not amount or not crypto_currency:
                messages.error(request, "Please provide both amount and cryptocurrency")
                return redirect("core:crypto-deposit")
                
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValidationError("Amount must be greater than zero")
                    
                # ... (NOWPayments logic commented out)
                
                # Create pending transaction
                transaction = Deposit.objects.create(
                    user=request.user,
                    amount=amount,
                    status="pending",
                    # description=f"Crypto deposit via {crypto_currency}",
                    account=account
                )
                
                return render(request, "core/deposit/crypto_payment.html", {
                    "account": account,
                    # "cryptocurrencies": CRYPTO_CURRENCIES,
                    # "payment_info": payment_info
                })
                
            except (ValueError, ValidationError) as e:
                messages.error(request, str(e))
                return redirect("core:crypto-deposit")
            except Exception as e:
                messages.error(request, f"Error processing crypto payment: {str(e)}")
                return redirect("core:crypto-deposit")
                
        return render(request, "core/deposit/crypto_payment.html", {
            "account": account,
            # "cryptocurrencies": CRYPTO_CURRENCIES
        })
        
    except Account.DoesNotExist:
        messages.error(request, "No account found.")
        return redirect("account:dashboard")