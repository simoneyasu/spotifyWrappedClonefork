from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from functionality.views import get_user_data


def dashboard(request):
    return render(request, 'wrap/dashboard.html')


def your_wrap(request):
    access_token = request.session.get('access_token', None)
    if not access_token:
        return redirect('login')

    # Get user data
    user_data = get_user_data(access_token)

    # Pass user data to the template
    return render(request, 'wrap/your_wrap.html', user_data)