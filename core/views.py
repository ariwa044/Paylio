from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'core/index.html')


# Static Information Pages
def about_us(request):
    return render(request, 'core/pages/about_us.html')


def terms_of_service(request):
    return render(request, 'core/pages/terms_of_service.html')


def privacy_policy(request):
    return render(request, 'core/pages/privacy_policy.html')


def contact_us(request):
    return render(request, 'core/pages/contact_us.html')