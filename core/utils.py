"""
Core utility functions for the banking application.
"""
from core.models import AccountFreeze
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings


def is_account_frozen(account):
    """
    Check if an account has an active freeze.
    
    Args:
        account: The Account instance to check
        
    Returns:
        tuple: (is_frozen: bool, freeze_record: AccountFreeze or None)
    """
    if account is None:
        return False, None
    
    active_freeze = AccountFreeze.objects.filter(
        account=account,
        is_active=True
    ).first()
    
    return active_freeze is not None, active_freeze


def get_freeze_reason_display(freeze_record):
    """
    Get a user-friendly display of the freeze reason.
    
    Args:
        freeze_record: AccountFreeze instance
        
    Returns:
        str: Human-readable freeze reason
    """
    if freeze_record is None:
        return ""
    
    reason_map = {
        'suspicious_activity': 'Suspicious Activity Detected',
        'user_request': 'Account Frozen by User Request',
        'compliance': 'Compliance Review Required',
        'security': 'Security Concern',
        'other': 'Account Under Review',
    }
    
    return reason_map.get(freeze_record.reason, 'Account Frozen')


def send_html_email(subject, recipient_list, context, template_path='emails/notification_email.html'):
    """
    Send an HTML email using a template.
    
    Args:
        subject (str): Email subject
        recipient_list (list): List of recipient emails
        context (dict): Context data for template (must include 'message')
        template_path (str): Path to HTML template
    """
    # Ensure subject is in context for header if not present
    if 'subject_header' not in context:
        context['subject_header'] = subject
        
    html_message = render_to_string(template_path, context)
    plain_message = strip_tags(html_message)
    email_from = settings.DEFAULT_FROM_EMAIL
    
    try:
        send_mail(
            subject,
            plain_message,
            email_from,
            recipient_list,
            html_message=html_message,
            fail_silently=True
        )
        return True
    except Exception:
        return False
