from collections import Counter
from datetime import datetime, timedelta
from logging import exception
import random
import requests

from django.http import JsonResponse
from django.shortcuts import render
from functionality.forms import ContactForm
from django.http import HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages

from register.views import refresh_spotify_token

'''
gets user data (top tracks, top artist, top genres, and total listened time)

args: access_token (str): Spotify API access token. time_range (str): Time range for data (e.g., short, medium, long-term)

returns: dict: Dictionary containing top tracks, artists, genres, and total minutes listened
'''


def get_User_Data(access_token, user_profile, time_range='long_term'):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Fetch top tracks
    top_tracks_url = f"https://api.spotify.com/v1/me/top/tracks?limit=5&time_range={time_range}"
    top_tracks_response = requests.get(top_tracks_url, headers=headers)

    if top_tracks_response.status_code == 401:  # Unauthorized, refresh token once
        new_token = refresh_spotify_token(user_profile)
        headers['Authorization'] = f'Bearer {new_token}'
        top_tracks_response = requests.get(top_tracks_url, headers=headers)  # Retry with new token

    # Check for successful response or raise an error
    if top_tracks_response.status_code != 200:
        raise Exception(f"Error fetching top tracks from Spotify API: {top_tracks_response.status_code}")

    top_tracks_json = top_tracks_response.json().get('items', [])
    top_tracks = [track['name'] for track in top_tracks_json]

    # Fetch top artists with the (possibly refreshed) token
    top_artists_url = f"https://api.spotify.com/v1/me/top/artists?limit=5&time_range={time_range}"
    top_artists_response = requests.get(top_artists_url, headers=headers)

    if top_artists_response.status_code != 200:
        raise Exception(f"Error fetching top artists from Spotify API: {top_artists_response.status_code}")

    top_artists_json = top_artists_response.json().get('items', [])
    top_artists = [artist['name'] for artist in top_artists_json]

    # Process top genres and total listening minutes
    top_genres = get_top_genres(top_artists_json)
    total_mins_listened = get_total_minutes_listened(headers, time_range)

    return {
        "top_tracks": top_tracks,
        "top_artists": top_artists,
        "top_genres": top_genres,
        "total_mins_listened": total_mins_listened
    }
'''
gets top genres from a list of artists

args: artists (list): List of artist data containing genres

returns: list: List of top genres and their counts
'''
def get_top_genres(artists):
    all_genres = [genre for artist in artists for genre in artist['genres']]
    genre_counts = Counter(all_genres)
    top_genres = genre_counts.most_common(5)  # Get top 5 genres
    return [{"genre": genre, "count": count} for genre, count in top_genres]

'''
gets total minutes listened for a user

args: headers (dict): Headers with authorization info for Spotify API

returns: str: Total minutes listened, rounded to the nearest integer
'''


def get_total_minutes_listened(headers, time_range):
    # Spotify API endpoint for top tracks
    url = "https://api.spotify.com/v1/me/top/tracks"
    params = {
        "time_range": time_range,  # Short, medium, or long-term time range
        "limit": 50  # Maximum number of tracks per request
    }

    total_duration_ms = 0
    next_url = url
    request_count = 0  # Track the number of requests made
    max_requests = 15

    while next_url and request_count < max_requests:
        response = requests.get(next_url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from Spotify API: {response.status_code}")

        data = response.json()

        # Sum up durations of tracks in milliseconds
        total_duration_ms += sum(track['duration_ms'] for track in data.get('items', []))

        # Continue paginating if more data is available
        next_url = data.get('next')
        request_count += 1  # Increment the request counter

    # Convert milliseconds to minutes
    total_minutes = total_duration_ms / (1000 * 60)

    return round(total_minutes)
'''
contact form to send email (forget my password & contact developers)

args: request (HttpRequest): HTTP request object containing form data

returns: HttpResponse: Renders contact form page with success or error messages
'''
def contact_form(request):
    form = ContactForm()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = f"Message from {form.cleaned_data['name']}"
            message = form.cleaned_data['message']
            recipient_email = "spotifyWrappedClone@gmail.com"
            # error checking
            if recipient_email == None:
                raise exception('Error! The email is invalid') # invalid email
            try:
                send_mail(
                    subject,
                    message,
                    'spotifyWrappedClone@gmail.com', # will send to the dedicated email I created
                    [recipient_email],
                    fail_silently=False,
                )
                messages.success(request, "Success! Message sent.")
                form = ContactForm()  # Clear the form after successful submission
            except Exception as e:
                messages.error(request, f"Failed to send message: {e}")

    return render(request, 'functionality/development_process.html', {'form': form})
