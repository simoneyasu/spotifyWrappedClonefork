
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.utils import timezone
from django.conf import settings
from .models import UserProfile
import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# Create your views here.

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created! You can now log in.')
            return redirect('login')
        else:
            # Handle invalid form submission (e.g., email already exists)
            messages.error(request, 'There was a problem with your registration. Please fix the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to a home page or any other page
    else:
        form = CustomAuthenticationForm()
    return render(request, 'register/login.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        # Delete the user account if the form is submitted
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('login')  # Redirect to login or homepage after deletion
    return render(request, 'register/delete_account.html')

@login_required
def profile(request):
    return render(request, 'register/profile.html', {
        'user': request.user  # Pass the current user to the template
    })

def home(request):
    return render(request, 'register/home.html')

def get_spotify_token(code):
    url = "https://accounts.spotify.com/api/token"
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:8000/callback',
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'client_secret': settings.SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    return response.json()

def spotify_callback(request):
    code = request.GET.get('code')
    token_data = get_spotify_token(code)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_profile.access_token = token_data['access_token']
    user_profile.refresh_token = token_data['refresh_token']
    user_profile.token_expires_at = timezone.now() + timezone.timedelta(seconds=token_data['expires_in'])
    user_profile.save()
    return redirect('home')


def landing_view(request):
    return render(request, 'register/landing.html')


