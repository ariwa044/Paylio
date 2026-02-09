from django.urls import path
from .views import RegisterView, LoginView, LogoutView, otp_verification, resend_otp



app_name = 'userauths'






urlpatterns = [
    path("sign-up/",RegisterView, name='sign-up'),
    path("sign-in/",LoginView, name='sign-in'),
    path("sign-out/",LogoutView, name='sign-out'),
    path("otp-verification/", otp_verification, name='otp-verification'),
    path("resend-otp/", resend_otp, name='resend-otp'),

]
