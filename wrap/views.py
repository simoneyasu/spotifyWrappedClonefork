from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from functionality.views import get_User_Data


def dashboard(request):
    return render(request, 'wrap/dashboard.html')


def your_wrap(request):
    access_token = request.session.get('access_token', None)
    if not access_token:
        return redirect('login')

    # Get user data
    user_data = get_User_Data(access_token)

    # Pass user data to the template
    return render(request, 'wrap/your_wrap.html', user_data)

def test_wrap(request):
    return render(request, 'wrap/your_wrap.html')