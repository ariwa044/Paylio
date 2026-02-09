from django.shortcuts import render, redirect
from .forms import UserRegisterForm
from django.contrib.auth import authenticate, login, logout
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib import messages
from .models import User, UserDevice
import uuid
# Create your views here.



import random
from django.core.mail import send_mail
from django.core.mail import send_mail
from django.conf import settings
from core.utils import send_html_email

def RegisterView(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Store registration data in session instead of creating user
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            request.session['registration_data'] = {
                'email': email,
                'password': password,
                'username': email
            }
            
            # Generate OTP
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            
            # Clear any stale user_id from session
            if 'user_id' in request.session:
                del request.session['user_id']
            
            # Send Email with error handling
            try:
                subject = 'Your OTP for Account Verification'
                recipient_list = [email]
                print(f"DEBUG: Attempting to send email to {email}")
                send_html_email(subject, recipient_list, {'otp': otp}, template_path='userauths/email_otp.html')
                print(f"DEBUG: Email sent successfully to {email}")
                messages.success(request, f"OTP sent to {email}. Please verify.")
            except Exception as e:
                print(f"DEBUG: Email sending failed with error: {e}")
                messages.error(request, f"Failed to send OTP email: {e}")
                # Don't redirect, let them see the error
                return render(request, 'userauths/sign-up.html', {'form': form})
            
            return redirect("userauths:otp-verification")
        else:
            # Check if user exists but is inactive (failed previous sign-up)
            email = request.POST.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                    if not user.is_active:
                        # Resend OTP
                        otp = random.randint(100000, 999999)
                        request.session['otp'] = otp
                        request.session['user_id'] = user.id
                        
                        subject = 'Resend: Your OTP for Account Verification'
                        recipient_list = [user.email]
                        send_html_email(subject, recipient_list, {'otp': otp}, template_path='userauths/email_otp.html')
                        
                        messages.info(request, f"Account exists but is inactive. New OTP sent to {user.email}.")
                        return redirect("userauths:otp-verification")
                except User.DoesNotExist:
                    pass
            # Form is invalid, render with errors
            return render(request, 'userauths/sign-up.html', {'form': form})

    if request.user.is_authenticated:
        messages.warning(request, f"You are already logged in.")
        return redirect("account:dashboard")

    form = UserRegisterForm()
    return render(request,'userauths/sign-up.html',{'form':form})

def otp_verification(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        if 'otp' in request.session:
            session_otp = request.session['otp']
            
            if int(otp_input) == int(session_otp):
                user = None
                
                # Check if verifying existing user or new registration
                if 'user_id' in request.session:
                    user_id = request.session['user_id']
                    user = User.objects.get(id=user_id)
                    user.is_active = True
                    user.save()
                    del request.session['user_id']
                
                elif 'registration_data' in request.session:
                    data = request.session['registration_data']
                    user = User.objects.create_user(
                        username=data['username'],
                        email=data['email'],
                        password=data['password']
                    )
                    user.is_active = True
                    user.save()
                    del request.session['registration_data']
                
                if user:
                    # Device Tracking
                    device_id = str(uuid.uuid4())
                    UserDevice.objects.create(user=user, device_id=device_id)
                    
                    # Clear session OTP
                    del request.session['otp']
                    
                    login(request, user)
                    messages.success(request, "Identity verified successfully!")
                    
                    response = redirect("account:dashboard")
                    response.set_cookie('device_id', device_id, max_age=365*24*60*60) # 1 year cookie
                    return response
                else:
                    messages.error(request, "Session error. Please try again.")
                    return redirect("userauths:sign-up")
            else:
                messages.error(request, "Invalid OTP. Please try again.")
        else:
            messages.error(request, "Session expired. Please register or login again.")
            return redirect("userauths:sign-in")
            
    return render(request, "userauths/otp-verification.html")

def resend_otp(request):
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        try:
            user = User.objects.get(id=user_id)
            email = user.email
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("userauths:sign-in")
    elif 'registration_data' in request.session:
        email = request.session['registration_data']['email']
    else:
        messages.error(request, "Session expired.")
        return redirect("userauths:sign-in")
        
    # Generate new OTP
    otp = random.randint(100000, 999999)
    request.session['otp'] = otp
    
    # Send Email
    subject = 'Resend: Your OTP for Account Verification'
    recipient_list = [email]
    send_html_email(subject, recipient_list, {'otp': otp}, template_path='userauths/email_otp.html')
    
    messages.success(request, f"New OTP sent to {email}.")
    return redirect("userauths:otp-verification")




def LoginView(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # First check if user exists
            user = User.objects.get(email=email)
            # Then authenticate
            auth_user = authenticate(request, email=email, password=password)

            if auth_user is not None:
                # Check for device cookie
                device_id_cookie = request.COOKIES.get('device_id')
                
                if device_id_cookie:
                    device = UserDevice.objects.filter(user=auth_user, device_id=device_id_cookie).first()
                    if device:
                        # Known device, login
                        device.save() # Updates last_login automatically
                        login(request, auth_user)
                        messages.success(request, "Successfully logged in!")
                        return redirect('account:dashboard')
                
                # Unknown device or no cookie -> OTP
                # Generate OTP
                otp = random.randint(100000, 999999)
                request.session['otp'] = otp
                request.session['user_id'] = auth_user.id
                
                # Send Email
                subject = 'New Device Login Verification'
                recipient_list = [auth_user.email]
                send_html_email(subject, recipient_list, {'otp': otp}, template_path='userauths/email_otp.html')
                
                messages.warning(request, "New device detected. Please verify your identity.")
                return redirect("userauths:otp-verification")
                
            else:
                messages.warning(request, "Invalid password")
                return redirect("userauths:sign-in")
        except User.DoesNotExist:
            messages.warning(request, "No account found with this email address")
            return redirect("userauths:sign-in")

    if request.user.is_authenticated:
        messages.warning(request, "You Are Already Logged In")
        return redirect("account:dashboard")

    return render(request, "userauths/sign-in.html")



def LogoutView(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect('userauths:sign-in')