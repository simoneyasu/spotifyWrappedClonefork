from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model


from spotifyWrappedClone.settings import redirect_uri
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.utils import timezone
from django.conf import settings
from .models import UserProfile
import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SpotifyWrap

import openai

# Create your views here.

'''
Allows users to register for an account

args: request (HttpRequest): The HTTP request object

returns: HttpResponse: Renders the registration page or redirects to login
'''
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

'''
Allows users to log into their account

Args: request (HttpRequest): The HTTP request object

Returns: HttpResponse: Renders the login page or redirects to home
'''
def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to a home
    else:
        form = CustomAuthenticationForm()
    return render(request, 'register/login.html', {'form': form})

'''
Allows users to log into their account

args: request (HttpRequest): The HTTP request object

returns: HttpResponse: Renders account deletion page or redirects to login
'''
@login_required
def delete_account(request):
    if request.method == 'POST':
        # Delete the user account if the form is submitted
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('login')  # Redirect to login or homepage after deletion
    return render(request, 'register/delete_account.html')

'''
Allows users to view their profile. Shows their email and password

args: request (HttpRequest): The HTTP request object

returns: HttpResponse: Renders the profile page
'''
@login_required
def profile(request):
    return render(request, 'register/profile.html', {
        'user': request.user  # Pass the current user to the template
    })

'''
Brings to home page

args: request (HttpRequest): The HTTP request object

returns: HttpResponse: Renders the home page
'''
def home(request):
    return render(request, 'register/home.html')

'''
gets authorization code for an access token and refreshes token from Spotify

args: code (str): Authorization code from Spotify

returns: dict: Token data including access and refresh tokens
'''
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

'''
retrieves and stores Spotify tokens in session

args: request (HttpRequest): The HTTP request object

returns: HttpResponseRedirect: Redirects to fetch_wrap_data view
'''
def spotify_callback(request):
    code = request.GET.get('code')
    token_data = get_spotify_token(code)

    # access_token& refresh_token store at session
    request.session['access_token'] = token_data['access_token']
    request.session['refresh_token'] = token_data['refresh_token']

    # move to logic to get wrap1 data
    return redirect('fetch_wrap_data')

'''
landing page

args: request (HttpRequest): The HTTP request object

returns: HttpResponse: Renders the landing page
'''
def landing_view(request):
    return render(request, 'register/landing.html')

'''
allows users to log into their Spotify account

args: request (HttpRequest): The HTTP request object.

returns: HttpResponseRedirect: Redirects to Spotify authorization URL.
'''
def spotify_login(request):
    # Spotify OAuth URL creation
    spotify_auth_url = f"https://accounts.spotify.com/authorize?client_id={settings.SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={settings.SPOTIFY_REDIRECT_URI}&scope=user-top-read"

    return redirect(spotify_auth_url)

'''
uses Spotify API to get data

args: request (HttpRequest): The HTTP request object.

returns: HttpResponseRedirect: Redirects to view_wraps page.
'''
@login_required
def fetch_wrap_data(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('spotify_login') # access_token(X) -> login

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # request wrap1 data using spotify api
    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers)


    wrap_data = response.json()


    # store wrap1 data into session storage
    request.session['wrap_data'] = wrap_data

    # redirect to screen that shows wrap1 data
    return redirect('dashboard')


'''
Refreshes the Spotify access token if expired.

args: user_profile (UserProfile): The user's profile containing tokens.
'''
def refresh_spotify_token(user_profile):
    if timezone.now() > user_profile.token_expires_at:
        url = "https://accounts.spotify.com/api/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': user_profile.refresh_token,
            'client_id': settings.SPOTIFY_CLIENT_ID,
            'client_secret': settings.SPOTIFY_CLIENT_SECRET,
        }
        response = requests.post(url, data=data)
        token_data = response.json()
        user_profile.access_token = token_data['access_token']
        user_profile.token_expires_at = timezone.now() + timezone.timedelta(seconds=token_data['expires_in'])
        user_profile.save()
