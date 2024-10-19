
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
            return redirect('spotify_login')  # Redirect to a spotify login
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

@login_required
def get_spotify_token(code):
    url = "https://accounts.spotify.com/api/token"
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'client_secret': settings.SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    return response.json()

@login_required
def spotify_callback(request):
    code = request.GET.get('code')
    token_data = get_spotify_token(code)

    # access_token& refresh_token store at session
    request.session['access_token'] = token_data['access_token']
    request.session['refresh_token'] = token_data['refresh_token']

    # move to logic to get wrap data
    return redirect('fetch_wrap_data')


def landing_view(request):
    return render(request, 'register/landing.html')

@login_required
def spotify_login(request):
    # Spotify OAuth URL creation
    spotify_auth_url = f"https://accounts.spotify.com/authorize?client_id={settings.SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={settings.SPOTIFY_REDIRECT_URI}&scope=user-top-read"

    return redirect(spotify_auth_url)

@login_required
def fetch_wrap_data(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('spotify_login') # access_token(X) -> login

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # request wrap data using spotify api
    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers)
    wrap_data = response.json()

    # store wrap data into session storage
    request.session['wrap_data'] = wrap_data

    # redirect to screen that shows wrap data
    return redirect('view_wraps')

@login_required
def view_wraps(request):
    wrap_data = request.session.get('wrap_data', [])
    return render(request, 'view_wraps.html', {'wrap_data': wrap_data})