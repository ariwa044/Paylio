"""
Core utility functions for the banking application.
"""
from core.models import AccountFreeze

import os
import resend
from django.template.loader import render_to_string

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
    Send an HTML email using Resend API.
    
    Args:
        subject (str): Email subject
        recipient_list (list): List of recipient emails
        context (dict): Context data for template (must include 'message')
        template_path (str): Path to HTML template
    """
    # Initialize Resend API key
    resend.api_key = os.environ.get("RESEND_API_KEY")

    # Ensure subject is in context for header if not present
    if 'subject_header' not in context:
        context['subject_header'] = subject
        
    html_message = render_to_string(template_path, context)
    email_from = os.environ.get("DEFAULT_FROM_EMAIL", "onboarding@resend.dev")
    
    try:
        # Convert recipient_list to single string if it's a list (Resend expects list or string)
        # To be safe, we'll iterate or pass as is if Resend supports list. 
        # Resend Python SDK supports list of strings for 'to'.
        
        params = {
            "from": email_from,
            "to": recipient_list,
            "subject": subject,
            "html": html_message,
        }

        email = resend.Emails.send(params)
        print(f"Resend API Response: {email}") # Debugging
        return True
    except Exception as e:
        print(f"Resend API Error: {e}") # Debugging
        return False
