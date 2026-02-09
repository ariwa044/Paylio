from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Transfer, Deposit, Withdrawal, PaymentRequest
from django.contrib import messages
from itertools import chain

@login_required
def transaction_list(request):
    """Display filtered and paginated transaction list."""
    user = request.user
    
    # Initialize querysets
    transfers = Transfer.objects.filter(Q(user=user) | Q(receiver=user))
    deposits = Deposit.objects.filter(user=user)
    withdrawals = Withdrawal.objects.filter(user=user)
    requests = PaymentRequest.objects.filter(Q(sender=user) | Q(receiver=user))

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        transfers = transfers.filter(
            Q(transaction_id__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(amount__icontains=search_query)
        )
        deposits = deposits.filter(
            Q(transaction_id__icontains=search_query) |
            Q(amount__icontains=search_query)
        )
        withdrawals = withdrawals.filter(
            Q(transaction_id__icontains=search_query) |
            Q(amount__icontains=search_query)
        )
        requests = requests.filter(
            Q(transaction_id__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(amount__icontains=search_query)
        )

    # Filter by transaction type
    transaction_type = request.GET.get('type')
    transactions = []
    
    if transaction_type == 'transfer':
        transactions = list(transfers)
    elif transaction_type == 'deposit':
        transactions = list(deposits)
    elif transaction_type == 'withdraw' or transaction_type == 'withdrawal':
        transactions = list(withdrawals)
    elif transaction_type == 'request':
        transactions = list(requests)
    else:
        # 'all' or None -> combine everything
        transactions = list(chain(transfers, deposits, withdrawals, requests))
    
    # Sort by date
    transactions.sort(key=lambda x: x.date, reverse=True)
    
    # Filter by status (Post-processing since status field is common)
    status = request.GET.get('status')
    if status and status != 'all':
        transactions = [t for t in transactions if t.status == status]
    
    # Filter by date range (Post-processing)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        transactions = [t for t in transactions if str(t.date.date()) >= date_from]
    if date_to:
        transactions = [t for t in transactions if str(t.date.date()) <= date_to]
    
    # Pagination
    paginator = Paginator(transactions, 20)  # Show 20 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'transactions': page_obj,
        'current_type': transaction_type,
        'current_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'transaction/transaction-list.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """Display detailed transaction information."""
    # Try all models
    transaction = None
    try:
        transaction = Transfer.objects.get(transaction_id=transaction_id)
    except Transfer.DoesNotExist:
        try:
            transaction = Deposit.objects.get(transaction_id=transaction_id)
        except Deposit.DoesNotExist:
            try:
                transaction = Withdrawal.objects.get(transaction_id=transaction_id)
            except Withdrawal.DoesNotExist:
                try:
                    transaction = PaymentRequest.objects.get(transaction_id=transaction_id)
                except PaymentRequest.DoesNotExist:
                    messages.warning(request, "Transaction not found")
                    return redirect("core:transaction-list")
    
    context = {
        "transaction": transaction,
    }
    
    return render(request, 'transaction/transaction_detail.html', context)