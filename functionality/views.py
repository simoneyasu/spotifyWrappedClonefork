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

'''
gets user data (top tracks, top artist, top genres, and total listened time)

args: access_token (str): Spotify API access token. time_range (str): Time range for data (e.g., short, medium, long-term)

returns: dict: Dictionary containing top tracks, artists, genres, and total minutes listened
'''
def get_User_Data(access_token, time_range = 'long_term'):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    top_tracks_response = requests.get(
        #adds time_range to api call
        f"https://api.spotify.com/v1/me/top/tracks?limit=5&time_range={time_range}",
        headers=headers
    )
    top_tracks_json = top_tracks_response.json().get('items', [])
    top_tracks = []

    for track in top_tracks_json:
        top_tracks.append(track['name'])
    top_artists_response = requests.get(
        f"https://api.spotify.com/v1/me/top/artists?limit=5&time_range={time_range}",
        headers=headers
    )
    top_artists_json = top_artists_response.json().get('items', [])
    top_artists = []
    for artist in top_artists_json:
        top_artists.append(artist['name'])

    top_genres = get_top_genres(top_artists_json)
    total_mins_listened = get_total_minutes_listened(headers, time_range)
    return {"top_tracks":top_tracks,
            "top_artists":top_artists,
            "top_genres":top_genres,
            "total_mins_listened":total_mins_listened}

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

'''
gets random tracks

args:   headers (dict): Headers with authorization info for Spotify API
        limit (int): Number of tracks to retrieve (default is 20)
        listSize (int): Number of random tracks to return (default is 5)

returns: list: List of randomly selected tracks with name, artists, and URI
'''
def get_random_tracks(headers, limit=20, listSize=5):

    url = "https://api.spotify.com/v1/me/player/recently-played"
    params = {
        "limit": limit
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        recent_tracks = [
            {
                "name": item["track"]["name"],
                "artists": [artist["name"] for artist in item["track"]["artists"]],
                "uri": item["track"]["uri"]
            }
            for item in data["items"]
        ]

        # Choose a random subset of tracks
        random_tracks = random.sample(recent_tracks, min(listSize, len(recent_tracks)))
        return random_tracks
    else:
        print("Failed to retrieve recently played tracks:", response.status_code, response.text)
        return []

'''
gets random tacks and parses through them

args: request (HttpRequest): HTTP request object

returns: HttpResponse: Renders the wrap page with track IDs
'''
def random_track_parse(request):
    # Assuming random_tracks is a list of song URIs (like "spotify:track:<track_id>")
    random_tracks = get_random_tracks()  # Replace with your function to fetch random tracks

    # Extract just the track IDs (last part of each URI)
    track_ids = [track['uri'].split(':')[-1] for track in random_tracks]

    context = {
        'track_ids': track_ids,
        # Add any other context data here
    }
    return render(request, 'wrap/your_wrap.html', context)