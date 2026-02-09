from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Sum
from .forms import KYCForm
from .models import KYC, Account
from django.contrib import messages
from core.forms import CreditCardForm
from core.models import CreditCard, Transfer, PaymentRequest
from core.utils import is_account_frozen, get_freeze_reason_display, send_html_email
# Create your views here.


def account(request):
    user = request.user

    if request.user.is_authenticated:
        try:
            kyc = KYC.objects.get(user=user)
        except:
            messages.warning(request, "You Need To Submit Your KYC")
            return redirect("account:kyc-form")

        account = Account.objects.get(user=user)
        # Check if KYC is confirmed
        if not account.kyc_confirmed or account.account_status == "pending":
            return redirect("account:kyc-pending")
    else:
        messages.warning(request, "You Need To Login")
        return redirect("userauths:sign-in")
    credit_cards = CreditCard.objects.filter(user=user).order_by("-id")
    context = {
        'account':account,
        'kyc':kyc,
        'credit_cards': credit_cards
    }
    return render(request, 'account/account.html', context)



@login_required
def kyc_registration(request):
    user = request.user
    if not user.is_authenticated:
        messages.warning(request, "You Need To Login")
        return redirect("userauths:sign-in")
        
    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        messages.warning(request, "Account not found.")
        return redirect("account:dashboard")


    try:
        kyc = KYC.objects.get(user=user)

    except:
        kyc = None
    if request.method == "POST":    
        form = KYCForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = user
            new_form.account = account
            new_form.save()
            # Update Account Status
            account.account_status = "pending"
            account.kyc_submitted = True
            account.save()
            
            # Send Email to User
            subject = 'KYC Submitted Successfully'
            send_html_email(subject, [user.email], {'user': user}, template_path='account/email_kyc_submitted.html')

            # Send Email to Admin (You need to configure ADMIN_EMAIL in settings or use hardcoded/superuser email)
            # For now, we'll try to find a superuser
            from userauths.models import User as UserModel
            admins = UserModel.objects.filter(is_superuser=True)
            admin_emails = [admin.email for admin in admins if admin.email]
            
            if admin_emails:
                admin_subject = 'New KYC Submission'
                send_html_email(admin_subject, admin_emails, {'user': user}, template_path='account/email_kyc_admin_notification.html')

            messages.success(request, "KYC Form submitted successfully. Your account is under review.")
            return redirect("account:kyc-pending")

    else:
        form = KYCForm(instance=kyc) 

    if request.method == "POST" and not form.is_valid():
        messages.error(request, "Form is invalid. Please check the fields below.") 

    context = {
        "account": account,
        "form": form,
        "kyc": kyc,

        }

    return render(request, "account/kyc-form.html", context) 

@login_required
def kyc_pending(request):
    return render(request, "account/kyc-pending.html")           





def Dashboard(request):
    user = request.user

    if request.user.is_authenticated:
        try:
            kyc = KYC.objects.get(user=user)
        except:
            messages.warning(request, "You Need To Submit Your KYC")
            return redirect("account:kyc-reg")
        
        # Recent transfers (sent)
        recent_transfer = Transfer.objects.filter(user=request.user, status="completed").order_by("-id")[:1]
        
        # Recent received transfers
        recent_recieved_transfer = Transfer.objects.filter(receiver=request.user).order_by("-id")[:1]


        sender_transaction = Transfer.objects.filter(user=request.user).order_by("-id")[:5]
        reciever_transaction = Transfer.objects.filter(receiver=request.user).order_by("-id")[:5]

        request_sender_transaction = PaymentRequest.objects.filter(sender=request.user)
        request_reciever_transaction = PaymentRequest.objects.filter(receiver=request.user)
        
        account = Account.objects.get(user=request.user)
        # Check if KYC is confirmed
        if not account.kyc_confirmed or account.account_status == "pending":
            return redirect("account:kyc-pending")
        credit_card = CreditCard.objects.filter(user=request.user).order_by("-id")

        if request.method == "POST":
            form = CreditCardForm(request.POST)
            if form.is_valid():
                new_form = form.save(commit=False)
                new_form.user = request.user
                new_form.save()

                card_id = new_form.card_id
                messages.success(request, "Card ADDED Successfully.")
                return redirect("account:dashboard")
        else:
            form = CreditCardForm()
        account = Account.objects.get(user=user)
        credit_card = CreditCard.objects.filter(user=user).order_by("-id")
        total_sent = Transfer.objects.filter(user=request.user, status="completed").aggregate(Sum('amount'))['amount__sum'] or 0
        total_received = Transfer.objects.filter(receiver=request.user, status="completed").aggregate(Sum('amount'))['amount__sum'] or 0

        context = {
            'account':account,
            'kyc':kyc,
            'form':form,
            "credit_card":credit_card,

            "sender_transaction":sender_transaction,
            "reciever_transaction":reciever_transaction,

            'request_sender_transaction':request_sender_transaction,
            'request_reciever_transaction':request_reciever_transaction,
            'recent_transfer':recent_transfer,
            'recent_recieved_transfer':recent_recieved_transfer,

            'total_sent': total_sent,
            'total_received': total_received,
        }
        
        # Check if account is frozen and add to context
        is_frozen, freeze_record = is_account_frozen(account)
        context['is_frozen'] = is_frozen
        if is_frozen:
            context['freeze_reason'] = get_freeze_reason_display(freeze_record)
            context['freeze_notes'] = freeze_record.notes if freeze_record else ''
        
        return render(request, 'account/dashboard.html', context)
    else:
        messages.warning(request, "You Need To Login")
        return redirect("userauths:sign-in")

@login_required
def pin_settings(request):
    user = request.user
    if not user.is_authenticated:
         messages.warning(request, "You Need To Login")
         return redirect("userauths:sign-in")

    try:
        account = Account.objects.get(user=user)
        kyc = KYC.objects.get(user=user)
    except:
        messages.warning(request, "Account or KYC not found.")
        return redirect("account:dashboard")

    if request.method == "POST":
        current_pin = request.POST.get('current_pin')
        new_pin = request.POST.get('new_pin')
        confirm_new_pin = request.POST.get('confirm_new_pin')

        if current_pin != account.pin_number:
            messages.error(request, "Current PIN is incorrect.")
        elif new_pin != confirm_new_pin:
            messages.error(request, "New PINs do not match.")
        elif len(new_pin) != 4 or not new_pin.isdigit():
             messages.error(request, "PIN must be 4 digits.")
        else:
            account.pin_number = new_pin
            account.save()
            messages.success(request, "PIN updated successfully.")
            return redirect('account:pin-settings')
    
    context = {
        'account': account,
        'kyc': kyc,
    }
    return render(request, 'account/pin-settings.html', context)
