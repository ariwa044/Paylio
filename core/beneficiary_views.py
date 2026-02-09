from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Beneficiary
from account.models import Account





@login_required
def delete_beneficiary(request, beneficiary_id):
    """Delete a beneficiary."""
    try:
        beneficiary = Beneficiary.objects.get(id=beneficiary_id, user=request.user)
        beneficiary.is_active = False
        beneficiary.save()
        messages.success(request, "Beneficiary removed successfully")
    except Beneficiary.DoesNotExist:
        messages.error(request, "Beneficiary not found")
    
    return redirect('core:beneficiary-list')


@login_required
def transfer_to_beneficiary(request, beneficiary_id):
    """Quick transfer to a saved beneficiary."""
    try:
        beneficiary = Beneficiary.objects.get(id=beneficiary_id, user=request.user, is_active=True)
        
        # Update last used timestamp
        beneficiary.last_used = timezone.now()
        beneficiary.save()
        
        # Redirect to transfer page with pre-filled account number
        return redirect('core:amount-transfare', account_number=beneficiary.account_number)
        
    except Beneficiary.DoesNotExist:
        messages.error(request, "Beneficiary not found")
        return redirect('core:beneficiary-list')
