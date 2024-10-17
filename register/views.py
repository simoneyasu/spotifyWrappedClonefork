
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.utils import timezone
from django.conf import settings
from .models import UserProfile
import requests

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in the user after registration
            return redirect('home')  # Redirect to a home page or any other page
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

