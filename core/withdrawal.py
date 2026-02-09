from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from account.models import Account
from .models import Withdrawal, Notification
from .utils import is_account_frozen, get_freeze_reason_display
from django.core.exceptions import ValidationError


@login_required
def initiate_withdrawal(request):
    """View to initiate a withdrawal request."""
    try:
        account = Account.objects.get(user=request.user)
        if not account.kyc_confirmed:
            messages.warning(request, "Please complete your KYC verification first.")
            return redirect("account:kyc-reg")
        
        if account.account_status != "active":
            messages.error(request, "Your account must be active to make withdrawals.")
            return redirect("account:dashboard")
        
        # Check if account is frozen
        is_frozen, freeze_record = is_account_frozen(account)
        if is_frozen:
            messages.error(request, f"Your account is frozen: {get_freeze_reason_display(freeze_record)}. Withdrawals are not allowed.")
            return redirect("account:account")
        
        if request.method == "POST":
            amount = request.POST.get("amount")
            bank_name = request.POST.get("bank_name")
            account_number = request.POST.get("account_number")
            account_name = request.POST.get("account_name")
            description = request.POST.get("description", "Bank Withdrawal")
            
            if not all([amount, bank_name, account_number, account_name]):
                messages.error(request, "Please fill in all fields")
                return redirect("core:initiate-withdrawal")
            
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValidationError("Amount must be greater than zero")
                
                if amount > account.account_balance:
                    messages.error(request, "Insufficient funds")
                    return redirect("core:initiate-withdrawal")
                
                # Create withdrawal transaction
                withdrawal_transaction = Withdrawal.objects.create(
                    user=request.user,
                    amount=amount,
                    status="pending",
                    account=account, # Provide account field
                    description=f"{description} - {bank_name} ({account_number})",
                    # sender/sender_account removed as Withdrawal model has user/account
                )
                
                # Create notification
                Notification.objects.create(
                    user=request.user,
                    notification_type="Debit Alert",
                    amount=amount
                )
                
                messages.success(request, "Withdrawal request submitted successfully")
                return redirect("core:confirm-withdrawal", transaction_id=withdrawal_transaction.transaction_id)
                
            except (ValueError, ValidationError) as e:
                messages.error(request, str(e))
                return redirect("core:initiate-withdrawal")
        
        return render(request, "core/withdrawal/initiate_withdrawal.html", {
            "account": account
        })
        
    except Account.DoesNotExist:
        messages.error(request, "No account found.")
        return redirect("account:dashboard")


@login_required
def confirm_withdrawal(request, transaction_id):
    """View to confirm withdrawal details before processing."""
    withdrawal = get_object_or_404(Withdrawal, 
                                   transaction_id=transaction_id,
                                   user=request.user)
    
    if withdrawal.status != "pending":
        messages.warning(request, "This withdrawal has already been processed.")
        return redirect("core:transaction-detail", transaction_id=transaction_id)
    
    if request.method == "POST":
        return redirect("core:process-withdrawal", transaction_id=transaction_id)
    
    return render(request, "core/withdrawal/confirm_withdrawal.html", {
        "withdrawal": withdrawal
    })


@login_required
@transaction.atomic
def process_withdrawal(request, transaction_id):
    """Process the withdrawal transaction."""
    withdrawal = get_object_or_404(Withdrawal, 
                                   transaction_id=transaction_id,
                                   user=request.user)
    
    if withdrawal.status != "pending":
        messages.warning(request, "This withdrawal has already been processed.")
        return redirect("core:transaction-detail", transaction_id=transaction_id)
    
    if request.method == "POST":
        pin_number = request.POST.get("pin_number")
        account = request.user.account
        
        if not pin_number:
            messages.error(request, "Please enter your PIN")
            return redirect("core:confirm-withdrawal", transaction_id=transaction_id)
        
        # Verify PIN
        if pin_number != account.pin_number:
            messages.error(request, "Incorrect PIN number")
            return redirect("core:confirm-withdrawal", transaction_id=transaction_id)
        
        # Check balance again
        if withdrawal.amount > account.account_balance:
            withdrawal.status = "failed"
            withdrawal.save()
            messages.error(request, "Insufficient funds")
            return redirect("core:withdrawal-failure", transaction_id=transaction_id)
        
        try:
            # Update withdrawal status to processing
            withdrawal.status = "processing"
            withdrawal.save()
            
            # Deduct from account balance
            account.account_balance -= withdrawal.amount
            account.save()
            
            # Mark as completed
            withdrawal.status = "completed"
            withdrawal.update = timezone.now()
            withdrawal.save()
            
            # Create success notification
            Notification.objects.create(
                user=request.user,
                notification_type="Debit Alert",
                amount=withdrawal.amount
            )
            
            messages.success(request, f"Withdrawal of ${withdrawal.amount} processed successfully")
            return redirect("core:withdrawal-success", transaction_id=transaction_id)
            
        except Exception as e:
            withdrawal.status = "failed"
            withdrawal.save()
            messages.error(request, f"Error processing withdrawal: {str(e)}")
            return redirect("core:withdrawal-failure", transaction_id=transaction_id)
    
    return redirect("core:confirm-withdrawal", transaction_id=transaction_id)


@login_required
def withdrawal_pending(request, transaction_id):
    """Display withdrawal pending page."""
    withdrawal = get_object_or_404(Withdrawal, 
                                   transaction_id=transaction_id,
                                   user=request.user,
                                   status="processing")
    
    return render(request, "core/withdrawal/withdrawal_pending.html", {
        "withdrawal": withdrawal
    })


@login_required
def withdrawal_success(request, transaction_id):
    """Display successful withdrawal completion page."""
    withdrawal = get_object_or_404(Withdrawal, 
                                   transaction_id=transaction_id,
                                   user=request.user,
                                   status="completed")
    
    return render(request, "core/withdrawal/withdrawal_success.html", {
        "withdrawal": withdrawal
    })


@login_required
def withdrawal_failure(request, transaction_id):
    """Display withdrawal failure page with reason."""
    withdrawal = get_object_or_404(Withdrawal, 
                                   transaction_id=transaction_id,
                                   user=request.user,
                                   status="failed")
    
    return render(request, "core/withdrawal/withdrawal_failure.html", {
        "withdrawal": withdrawal
    })
