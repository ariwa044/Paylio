from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import Account, CreditCard, Notification


@login_required
def all_cards(request):
    """Display all saved cards for the user."""
    account = get_object_or_404(Account, user=request.user)
    cards = CreditCard.objects.filter(user=request.user, card_status=True).order_by('-date')
    
    context = {
        "account": account,
        "cards": cards,
    }
    return render(request, 'credit_card/all_cards.html', context)


@login_required
def credit_card_detail(request, card_id):
    """View details of a specific saved card."""
    account = get_object_or_404(Account, user=request.user)
    credit_card = get_object_or_404(CreditCard, user=request.user, card_id=card_id)

    context = {
        "account": account,
        "credit_card": credit_card,
    }
    return render(request, 'credit_card/card_detail.html', context)


@login_required
@require_POST
def add_card(request):
    """Add a new card via AJAX or form POST."""
    try:
        # Get form data
        name = request.POST.get('card_holder', '').strip()
        number = request.POST.get('card_number', '').strip()
        month = request.POST.get('expiry_month', '').strip()
        year = request.POST.get('expiry_year', '').strip()
        cvv = request.POST.get('cvv', '').strip()
        card_type = request.POST.get('card_type', 'master').strip()
        
        # Billing address
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        country = request.POST.get('country', '').strip()
        
        # Validate required fields
        if not all([name, number, month, year, cvv]):
            messages.error(request, "Please fill in all required card details.")
            return redirect('account:dashboard')
        
        # Validate month/year
        try:
            month_int = int(month)
            year_int = int(year)
            if month_int < 1 or month_int > 12:
                raise ValueError("Invalid month")
        except ValueError:
            messages.error(request, "Invalid expiry date.")
            return redirect('account:dashboard')
        
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
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            notification_type="Added Credit Card"
        )
        
        messages.success(request, f"Card ending in {card.last_four} added successfully!")
        return redirect('account:dashboard')
        
    except Exception as e:
        messages.error(request, f"Error adding card: {str(e)}")
        return redirect('account:dashboard')


@login_required
def delete_card(request, card_id):
    """Delete a saved card."""
    credit_card = get_object_or_404(CreditCard, card_id=card_id, user=request.user)
    
    if request.method == 'POST':
        # Create notification before deleting
        Notification.objects.create(
            user=request.user,
            notification_type="Deleted Credit Card"
        )
        
        last_four = credit_card.last_four
        credit_card.delete()
        
        messages.success(request, f"Card ending in {last_four} deleted successfully.")
        return redirect('account:dashboard')
    
    # If GET request, show confirmation page
    context = {
        "credit_card": credit_card,
    }
    return render(request, 'credit_card/delete_confirm.html', context)
