from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.utils.timezone import now

from spotifywrappedclone.settings import redirect_uri, spotify_client_id, spotify_redirect_uri
from .forms import customusercreationform, customauthenticationform
from django.utils import timezone
from django.conf import settings
import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import userprofile

# create your views here.

'''
allows users to register for an account
args: request (httprequest): the http request object
returns: httpresponse: renders the registration page or redirects to login
'''
def register(request):
    if request.method == 'post':
        form = customusercreationform(request.post)
        if form.is_valid():
            form.save()
            messages.success(request, 'your account has been created! you can now log in.')
            return redirect('login')
        else:
            # handle invalid form submission (e.g., email already exists)
            messages.error(request, 'there was a problem with your registration. please fix the errors below.')
    else:
        form = customusercreationform()

    return render(request, 'register/register.html', {'form': form})

'''
allows users to log into their account
args: request (httprequest): the http request object
returns: httpresponse: renders the login page or redirects to home
'''
def login_view(request):
    if request.method == 'post':
        form = customauthenticationform(request, data=request.post)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # redirect to a home
    else:
        form = customauthenticationform()
    return render(request, 'register/login.html', {'form': form})

'''
allows users to log into their account
args: request (httprequest): the http request object
returns: httpresponse: renders account deletion page or redirects to login
'''
@login_required
def delete_account(request):
    if request.method == 'post':
        # delete the user account if the form is submitted
        user = request.user
        user.delete()
        messages.success(request, 'your account has been successfully deleted.')
        return redirect('login')  # redirect to login or homepage after deletion
    return render(request, 'register/delete_account.html')

'''
allows users to view their profile. shows their email and password
args: request (httprequest): the http request object
returns: httpresponse: renders the profile page
'''
@login_required
def profile(request):
    return render(request, 'register/profile.html', {
        'user': request.user  # pass the current user to the template
    })

'''
brings to home page
args: request (httprequest): the http request object
returns: httpresponse: renders the home page
'''
def home(request):
    return render(request, 'register/home.html')

'''
gets authorization code for an access token and refreshes token from spotify
args: code (str): authorization code from spotify
returns: dict: token data including access and refresh tokens
'''
def get_spotify_token(code):
    url = "https://accounts.spotify.com/api/token"
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.spotify_redirect_uri,
        'client_id': settings.spotify_client_id,
        'client_secret': settings.spotify_client_secret,
    }
    response = requests.post(url, data=data)
    response_data = response.json()
    print("access token scopes get_token:", response_data.get("scope"))

    return response.json()

'''
retrieves and stores spotify tokens in session
args: request (httprequest): the http request object
returns: httpresponseredirect: redirects to fetch_wrap_data view
'''
def spotify_callback(request):
    code = request.get.get('code')
    token_data = get_spotify_token(code)

    # access_token& refresh_token store at session
    request.session['access_token'] = token_data['access_token']
    request.session['refresh_token'] = token_data['refresh_token']
    # move to logic to get wrap1 data
    return redirect('fetch_wrap_data')

'''
landing page
args: request (httprequest): the http request object
returns: httpresponse: renders the landing page
'''
def landing_view(request):
    return render(request, 'register/landing.html')

'''
allows users to log into their spotify account
args: request (httprequest): the http request object.
returns: httpresponseredirect: redirects to spotify authorization url.
'''
def spotify_login(request):
    # spotify oauth url creation
    spotify_auth_url = (
        f"https://accounts.spotify.com/authorize?response_type=code&"
        f"client_id={spotify_client_id}&"
        f"redirect_uri={spotify_redirect_uri}&"
        f"scope="
        "user-library-read user-library-modify user-read-private user-read-email "
        "user-top-read user-read-recently-played user-follow-read user-follow-modify "
        "user-read-playback-state user-modify-playback-state streaming app-remote-control "
    )
    return redirect(spotify_auth_url)
def check_token_scopes(access_token):
    headers = {'authorization': f'bearer {access_token}'}
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    response_data = response.json()
    print(response_data)
    if response.status_code == 200:
        print("token is valid")
        print("scopes:", response.json().get('scope'))
    else:
        print("invalid token or missing scopes")
'''
uses spotify api to get data
args: request (httprequest): the http request object.
returns: httpresponseredirect: redirects to view_wraps page.
'''
@login_required
def fetch_wrap_data(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('spotify_login')  # redirect to login if no access token

    headers = {
        'authorization': f'bearer {access_token}'
    }

    # get user profile data from spotify api
    profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    if profile_response.status_code != 200:
        return redirect('spotify_login')  # redirect to login if profile fetch fails

    profile_data = profile_response.json()
    spotify_id = profile_data.get('id')  # get the spotify user id

    # check if userprofile exists, otherwise create it
    if not userprofile.objects.filter(user=request.user).exists():
        userprofile.objects.create(
            user=request.user,
            spotify_id=spotify_id,  # set the spotify user id
            access_token=access_token,
            refresh_token=request.session.get('refresh_token'),
            token_expires_at=now() + timedelta(hours=1)
        )

    # request wrap data using spotify api
    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers)
    if response.status_code != 200:
        return redirect('spotify_login')  # redirect to login if wrap fetch fails

    wrap_data = response.json()

    # store wrap data in session
    request.session['wrap_data'] = wrap_data

    # redirect to screen that shows wrap data
    return redirect('view_wraps')



'''
refreshes the spotify access token if expired.
args: user_profile (userprofile): the user's profile containing tokens.
'''
def refresh_spotify_token(user_profile):
    if timezone.now() > user_profile.token_expires_at:
        url = "https://accounts.spotify.com/api/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': user_profile.refresh_token,
            'client_id': settings.spotify_client_id,
            'client_secret': settings.spotify_client_secret,
        }
        response = requests.post(url, data=data)
        token_data = response.json()
        user_profile.access_token = token_data['access_token']
        user_profile.token_expires_at = timezone.now() + timezone.timedelta(seconds=token_data['expires_in'])
        user_profile.save()