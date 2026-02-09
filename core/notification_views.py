from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import Notification


@login_required
def notification_list(request):
    """Display all notifications for the logged-in user."""
    notifications = Notification.objects.filter(user=request.user).order_by('-date')
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'core/notifications/notification_list.html', context)


@login_required
def mark_notification_read(request, nid):
    """Mark a specific notification as read."""
    try:
        notification = Notification.objects.get(nid=nid, user=request.user)
        notification.is_read = True
        notification.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('core:notification-list')
    except Notification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Notification not found'})
        return redirect('core:notification-list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the logged-in user."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('core:notification-list')


@login_required
def get_unread_notifications(request):
    """AJAX endpoint to get unread notifications count and recent notifications."""
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-date')[:5]
    
    notifications_data = [{
        'nid': n.nid,
        'type': n.notification_type,
        'amount': str(n.amount),
        'date': n.date.strftime('%Y-%m-%d %H:%M'),
        'is_read': n.is_read
    } for n in notifications]
    
    return JsonResponse({
        'count': Notification.objects.filter(user=request.user, is_read=False).count(),
        'notifications': notifications_data
    })


@login_required
def delete_notification(request, nid):
    """Delete a specific notification."""
    try:
        notification = Notification.objects.get(nid=nid, user=request.user)
        notification.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('core:notification-list')
    except Notification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Notification not found'})
        return redirect('core:notification-list')
