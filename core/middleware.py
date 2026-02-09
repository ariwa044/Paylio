"""
Middleware for account freeze enforcement.
Redirects frozen users to the dashboard where the freeze overlay is shown.
"""
from django.shortcuts import redirect
from django.urls import reverse
from core.utils import is_account_frozen


class AccountFreezeMiddleware:
    """
    Middleware that checks if a user's account is frozen.
    If frozen, redirects them to the dashboard (which shows the freeze overlay).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only check for authenticated users
        if request.user.is_authenticated:
            # Check if user has an account
            if hasattr(request.user, 'account'):
                is_frozen, _ = is_account_frozen(request.user.account)
                
                if is_frozen:
                    current_path = request.path
                    
                    # Allow static files, admin, and media
                    if (current_path.startswith('/static/') or 
                        current_path.startswith('/admin/') or
                        current_path.startswith('/media/')):
                        return self.get_response(request)
                    
                    # Allow dashboard (where freeze overlay is shown)
                    if current_path == '/account/dashboard/' or current_path == '/account/dashboard':
                        return self.get_response(request)
                    
                    # Allow logout URLs
                    if 'sign-out' in current_path or 'logout' in current_path:
                        return self.get_response(request)
                    
                    # Redirect all other pages to dashboard
                    return redirect('account:dashboard')
        
        return self.get_response(request)
