from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from account.models import Account
from django.db.models import Q
from .models import Transfer, Notification, Beneficiary
from .utils import is_account_frozen, get_freeze_reason_display, send_html_email
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from userauths.models import User


@login_required
def transfer_selection(request):
    return render(request, "transfare/transfer-selection.html")

@login_required
def search_external_account(request):
    beneficiaries = Beneficiary.objects.filter(user=request.user).exclude(bank_name="Paylio")
    
    if request.method == "POST":
        account_number = request.POST.get('account_number')
        if account_number:
            return redirect('core:amount-transfare', account_number=account_number)
            
    context = {
        'beneficiaries': beneficiaries
    }
    return render(request, "transfare/search-external-account.html", context)

@login_required
def search_using_account(request):
    account = Account.objects.all()

    query = request.POST.get('account_number')
    if query:
        account = Account.objects.filter(
            Q(account_number = query)|
            Q(account_id = query)
                                         ).distinct()


    beneficiaries = Beneficiary.objects.filter(user=request.user, bank_name="Paylio")
    
    context = {
        'account':account,
        'query':query,
        'beneficiaries': beneficiaries
        }
    return render(request, "transfare/search-account.html", context)




@login_required
def AmountTranfare(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)

    except:
        account = None

    # Check if this account is already a beneficiary
    is_beneficiary = False
    target_account_number = account_number # argument
    
    if request.user.is_authenticated:
        # Check using target_account_number
        if Beneficiary.objects.filter(user=request.user, account_number=target_account_number).exists():
            is_beneficiary = True
            try:
                beneficiary = Beneficiary.objects.get(user=request.user, account_number=target_account_number)
                beneficiary_name = beneficiary.name
                beneficiary_bank = beneficiary.bank_name
            except:
                beneficiary_name = None
                beneficiary_bank = None
        else:
            beneficiary_name = None
            beneficiary_bank = None

    context = {
        "account":account,
        "is_beneficiary": is_beneficiary,
        "new_account_number": target_account_number, # Pass explicit account number for template
        "beneficiary_name": beneficiary_name,
        "beneficiary_bank": beneficiary_bank
    }    

    return render(request, 'transfare/amount-transfare.html', context)




@login_required
def AmountTranfareProcess(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)
        reciver = account.user
        reciver_account = account
        bank_name = "Paylio"
        name = reciver.kyc.full_name
        transfer_type = "internal"
    except Account.DoesNotExist:
        account = None
        reciver = None
        reciver_account = None
        bank_name = request.POST.get("bank_name")
        name = request.POST.get("name")
        transfer_type = "external"

    sender = request.user
    sender_account = request.user.account

    if request.method=="POST":
        amount = request.POST.get("amount-send")
        description = request.POST.get("description")

        # Check if sender account is frozen
        sender_frozen, sender_freeze = is_account_frozen(sender_account)
        if sender_frozen:
            messages.error(request, f"Your account is frozen: {get_freeze_reason_display(sender_freeze)}. Please contact support.")
            return redirect("account:account")
        
        # Check if receiver account is frozen (for internal transfers)
        if reciver_account:
            receiver_frozen, receiver_freeze = is_account_frozen(reciver_account)
            if receiver_frozen:
                messages.error(request, "The recipient's account is currently frozen. Transfer cannot be completed.")
                return redirect("core:search-account")

        if sender_account.account_balance >= Decimal(amount):
            new_transfer = Transfer.objects.create(
                user = request.user,
                amount = amount,
                account = sender_account,
                receiver = reciver,
                receiver_account = reciver_account,
                receiver_account_number = account_number,
                receiver_bank = bank_name,
                receiver_name = name,
                description = description,
                transfer_type = transfer_type,
                status = "processing",
            )

            new_transfer.save()
            transaction_id = new_transfer.transaction_id
            
            # Save as beneficiary if requested and not already one
            if request.POST.get("save_beneficiary") == "on":
                # Check if already exists to prevent duplicates
                if not Beneficiary.objects.filter(user=request.user, account_number=account_number).exists():
                    Beneficiary.objects.create(
                        user=request.user,
                        beneficiary_account=reciver_account,
                        account_number=account_number,
                        bank_name=bank_name,
                        name=name
                    )
                    messages.success(request, "Beneficiary saved successfully!")

            return redirect("core:transfare-confirmation", account_number, transaction_id)
        
        else:
            messages.warning(request, 'Insufficient fund')
            return redirect("core:amount-transfare", account_number)

    else:
        messages.warning(request, 'Error Occured, Try again later .')
        return redirect("account:account")

         


@login_required
def TransactionConfirmation(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        account = None

    try:
        transaction = Transfer.objects.get(transaction_id=transaction_id)
    except Transfer.DoesNotExist:
        messages.warning(request, 'Transfer does not exist')
        return redirect('account:account') 

    context = {
        'account':account,
        'transaction':transaction,
        'account_number': account_number
    }       
    
    return render(request, 'transfare/transaction-confirmation.html', context)




@login_required
def TransfarProcess(request,account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        reciver_account = account
    except Account.DoesNotExist:
        account = None
        reciver_account = None

    try:
        transaction = Transfer.objects.get(transaction_id=transaction_id)
    except Transfer.DoesNotExist:
        messages.warning(request, 'Transfer does not exist')
        return redirect('account:account')

    sender = request.user
    sender_account = request.user.account

    # Check for PIN lockout
    from datetime import timedelta
    from django.utils import timezone

    if sender_account.pin_lockout_until:
        if timezone.now() < sender_account.pin_lockout_until:
            # Still locked
            messages.warning(request, "Account locked due to too many failed PIN attempts. Try again in 30 minutes.")
            return redirect("account:dashboard")
        else:
            # Lockout period has expired - automatically reset
            sender_account.failed_pin_attempts = 0
            sender_account.pin_lockout_until = None
            sender_account.save()

    
    completed = False
    if request.method=="POST":
        pin_num = request.POST.get('pin-number')
        # print(pin_num)

        if pin_num == sender_account.pin_number:
            # Reset failed attempts on success
            sender_account.failed_pin_attempts = 0
            sender_account.pin_lockout_until = None
            sender_account.save()

            if transaction.transfer_type == "external":
                transaction.status = "pending"
                
                # Email Admins for external transfer approval
                try:
                    subject = f'New External Transfer Request: ${transaction.amount}'
                    message = f'User {sender.username} (Account: {sender_account.account_number}) has requested an external transfer of ${transaction.amount}.\nTransaction ID: {transaction.transaction_id}\n\nPlease review and approve.'
                    context = {
                        'subject_header': 'External Transfer Request',
                        'message': message
                    }
                    admins = User.objects.filter(is_superuser=True)
                    recipient_list = [admin.email for admin in admins]
                    send_html_email(subject, recipient_list, context)
                except:
                    pass
            else:
                transaction.status = "completed"
                
            transaction.save()

            sender_account.account_balance -= transaction.amount
            sender_account.save()
            
            # Only credit receiver if they exist (internal)
            if reciver_account:
                reciver_account.account_balance += transaction.amount
                reciver_account.save()
                
                Notification.objects.create(
                    amount=transaction.amount,
                    user=account.user,
                    notification_type="Credit Alert",
                    transaction_id=transaction.transaction_id
                )
            
            Notification.objects.create(
                user=sender,
                notification_type="Debit Alert",
                amount=transaction.amount,
                transaction_id=transaction.transaction_id
            )
            
            # Send Transaction Email to Sender
            try:
                subject = f'Debit Alert: -${transaction.amount}'
                message = f'You sent ${transaction.amount} to {transaction.receiver.kyc.full_name}.\nTransaction ID: {transaction.transaction_id}'
                context = {
                    'subject_header': 'Debit Alert',
                    'message': message
                }
                recipient_list = [sender.email]
                send_html_email(subject, recipient_list, context)
            except:
                pass 
                
            # Send Credit Email to Receiver (if internal)
            if reciver_account:
                try:
                    subject = f'Credit Alert: +${transaction.amount}'
                    message = f'You received ${transaction.amount} from {sender.kyc.full_name}.\nTransaction ID: {transaction.transaction_id}'
                    context = {
                        'subject_header': 'Credit Alert',
                        'message': message
                    }
                    recipient_list = [reciver.email]
                    send_html_email(subject, recipient_list, context)
                except:
                    pass

            messages.success(request, "Transfer Successfull.")
            if transaction.transfer_type == "external":
                return redirect("core:transfare-pending", account_number, transaction.transaction_id)
            else:
                return redirect("core:transfar-completed", account_number, transaction.transaction_id)
        else:
            # Increment failed attempts
            sender_account.failed_pin_attempts += 1
            if sender_account.failed_pin_attempts >= 5:
                sender_account.pin_lockout_until = timezone.now() + timedelta(minutes=30)
                messages.error(request, "Too many failed attempts. Account locked for 30 minutes.")
            else:
                messages.warning(request, f"Incorrect Pin Number. {5 - sender_account.failed_pin_attempts} attempts remaining.")
            
            sender_account.save()
            return redirect("core:transfare-confirmation", account_number ,transaction.transaction_id)
        
    else:
        messages.warning(request, "An Error occured, Try again later.")
        return redirect("account:account")    



@login_required
def TransfarCompleted(request ,account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        account = None
    
    try:
        transaction = Transfer.objects.get(transaction_id=transaction_id)
    except Transfer.DoesNotExist:
        messages.warning(request, 'Transfer does not exists')
        return redirect("account:account")
    
    context = {
        'account':account,
        'transaction':transaction
    } 
    return render(request, 'transfare/transfar-completed.html', context)

@login_required
def TransfarPending(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        account = None

    try:
        transaction = Transfer.objects.get(transaction_id=transaction_id)
    except Transfer.DoesNotExist:
        messages.warning(request, 'Transfer does not exist')
        return redirect('account:account')

    context = {
        'account': account,
        'transaction': transaction
    }
    return render(request, 'transfare/transfer-pending.html', context)    