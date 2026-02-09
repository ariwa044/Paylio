from django.urls import path
from .views import kyc_registration, account,Dashboard, pin_settings
from . import views



app_name = 'account'

urlpatterns = [
    path("",account , name='account'),
    path("dashboard",Dashboard , name='dashboard'),

    path("kyc-reg/",kyc_registration, name='kyc-reg'),
    path("kyc-pending/", views.kyc_pending, name='kyc-pending'),
    path("pin-settings/", pin_settings, name='pin-settings'),
  

]
