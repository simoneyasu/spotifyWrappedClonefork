from collections import Counter
from datetime import datetime, timedelta
from django.contrib.sites import requests
from django.http import JsonResponse
from django.shortcuts import render
from functionality.forms import ContactForm
from django.http import HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages


def get_User_Data(access_token, time_range):
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

def get_top_genres(artists):
    all_genres = [genre for artist in artists for genre in artist['genres']]
    genre_counts = Counter(all_genres)
    top_genres = genre_counts.most_common(5)  # Get top 5 genres
    return [{"genre": genre, "count": count} for genre, count in top_genres]



def get_total_minutes_listened(headers, time_range):
    # Spotify API endpoint for recently played tracks
    url = "https://api.spotify.com/v1/me/top/tracks"
    params = {
        "time_range": time_range,  # Short, medium, or long-term time range
        "limit": 50  # Maximum number of tracks per request
    }

    total_duration_ms = 0
    next_url = url
    request_count = 0  # To track the number of requests made
    max_requests = 15

    while next_url and request_count < max_requests:  # Failsafe: Stop after max_requests
        response = requests.get(next_url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from Spotify API: {response.status_code}")

        data = response.json()

        # Sum up the durations of tracks (in milliseconds)
        total_duration_ms += sum(track['duration_ms'] for track in data['items'])

        # If there is more data, continue paginating
        next_url = data.get('next')  # This provides the URL for the next page of data
        request_count += 1  # Increment the request counter

    # Convert milliseconds to minutes
    total_minutes = total_duration_ms / (1000 * 60)

    return total_minutes

    total_ms = 0
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to fetch data from Spotify API"}, status=400)

        data = response.json()
        items = data.get("items", [])

        if not items:
            break

        for item in items:
            total_ms += item["track"]["duration_ms"]

        # Update the 'after' parameter for the next request
        params["after"] = items[-1]["played_at"]

    total_minutes = total_ms / (1000 * 60)  # Convert milliseconds to minutes
    return round(total_minutes)

def contact_form(request):
    form = ContactForm()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = f"Message from {form.cleaned_data['name']}"
            message = form.cleaned_data['message']
            recipient_email = "spotifyWrappedClone@gmail.com"

            try:
                send_mail(
                    subject,
                    message,
                    'spotifyWrappedClone@gmail.com',
                    [recipient_email],
                    fail_silently=False,
                )
                messages.success(request, "Success! Message sent.")
                form = ContactForm()  # Clear the form after successful submission
            except Exception as e:
                messages.error(request, f"Failed to send message: {e}")

    return render(request, 'functionality/development_process.html', {'form': form})

