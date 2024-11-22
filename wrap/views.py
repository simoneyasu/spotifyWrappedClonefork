import uuid
from django.shortcuts import render, redirect, get_object_or_404

from functionality.views import get_User_Data
import openai
from django.conf import settings
from django.contrib.auth.decorators import login_required
from register.models import SpotifyWrap
from django.http import JsonResponse
import os
import requests
import base64
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from requests_oauthlib import OAuth1

from register.views import check_token_scopes

from openai import OpenAI
from django.core.exceptions import ObjectDoesNotExist


'''
Displays the dashboard showing recent Spotify Wraps for the logged-in user.

@param request: The HTTP request object.
@return: Rendered HTML page with the user's dashboard.
'''
@login_required
def dashboard(request):
    recent_wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'wrap/dashboard.html', {'user' : request.user, 'recent_wraps': recent_wraps})

'''
Displays the details of a specific Spotify Wrap.

@param request: The HTTP request object.
@param wrap_id: The unique identifier of the Spotify Wrap.
@return: Rendered HTML page with the wrap's details and user data.
'''
def your_wrap(request, wrap_id):
    spotify_wrap = get_object_or_404(SpotifyWrap, wrap_id=wrap_id)

    access_token = request.session.get('access_token', None)
    if not access_token:
        return redirect('login')

    time_range_mapping = {
        'small': 'short_term',
        'medium': 'medium_term',
        'large': 'long_term'
    }

    term = time_range_mapping.get(spotify_wrap.time_range)

    user_data = get_User_Data(access_token, term)

    context = {
        'user_data': user_data,
        'spotify_wrap': spotify_wrap,
        'token': access_token
    }

    return render(request, 'wrap/your_wrap.html', context)

'''
Displays a list of all Spotify Wraps for the logged-in user.

@param request: The HTTP request object.
@return: Rendered HTML page with a list of wraps and shareable URLs.
'''
@login_required
def view_wraps(request):
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')
    no_wraps = wraps.count() == 0

    share_urls = []
    for wrap in wraps:
        try:
            twitter_url = f"https://twitter.com/intent/tweet?text=Check out my Spotify Wrap: {wrap.name}&url={request.build_absolute_uri(reverse('your_wrap', kwargs={'wrap_id': wrap.wrap_id}))}"
            linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={request.build_absolute_uri(reverse('your_wrap', kwargs={'wrap_id': wrap.wrap_id}))}"
            share_urls.append({
                "name": wrap.name,
                "twitter_url": twitter_url,
                "linkedin_url": linkedin_url,
            })
        except Exception as e:
            print(f"Error building URL for wrap {wrap.name}: {e}")

    if no_wraps:
        return render(request, 'wrap/view_wraps.html', {
            'wraps': wraps,
            'no_wraps': no_wraps,
            'message': 'You do not have any Spotify Wraps yet. Please listen to music to generate your wraps.'
        })

    return render(request, 'wrap/view_wraps.html', {'wraps': wraps, 'no_wraps': no_wraps, 'share_urls': share_urls})


'''
Displays detailed information about a specific Spotify Wrap.

@param request: The HTTP request object.
@param wrap_id: The unique identifier of the Spotify Wrap.
@return: Rendered HTML page with detailed wrap information.
'''
@login_required
def wrap_detail(request, wrap_id):
    wrap = get_object_or_404(SpotifyWrap, wrap_id=wrap_id, user=request.user)

    # Convert track durations from milliseconds to "minutes:seconds"
    for track in wrap.data.get('tracks', []):
        duration_ms = track.get('duration', 0)
        minutes, seconds = divmod(duration_ms // 1000, 60)
        track['formatted_duration'] = f"{minutes}:{seconds:02}"

    return render(request, 'wrap/wrap_detail.html', {'wrap': wrap})

'''
Deletes a specific Spotify Wrap for the logged-in user.

@param request: The HTTP request object.
@param wrap_id: The unique identifier of the Spotify Wrap.
@return: Redirect to the wraps list page or an error response.
'''
@login_required
def delete_wrap(request, wrap_id):
    if request.method == "POST":
        try:
            wrap = get_object_or_404(SpotifyWrap, wrap_id=wrap_id, user=request.user)
            wrap.delete()
            return redirect('view_wraps')
        except Exception as e:
            print(f"Error deleting wrap: {e}")
            return redirect('view_wraps')
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


'''
Uses ChatGPT to analyze a Spotify Wrap and generate a description based on the music taste.

@param request: The HTTP request object.
@param wrap_id: The unique identifier of the Spotify Wrap.
@return: Rendered HTML page with analysis results.
'''
openai.api_key = settings.OPENAI_API_KEY

@login_required
def analyze_wrap(request, wrap_id):
    try:
        wrap = SpotifyWrap.objects.get(wrap_id=wrap_id, user=request.user)
    except ObjectDoesNotExist:
        return render(request, 'wrap/analyze_wrap.html', {
            'error': "No valid Wrap data available for analysis."
        })

    prompt = f"Based on my music taste from {wrap.year}, describe how someone with similar taste might dress, act, or think."

    friend_wrap_id = request.GET.get('friend_wrap_id')
    friend_wrap = None
    comparison_description = None

    if friend_wrap_id:
        try:
            friend_wrap = SpotifyWrap.objects.get(wrap_id=friend_wrap_id)
            comparison_description = f"Compared your wrap ({wrap.year}) with your friend's wrap ({friend_wrap.year})."
            prompt += f" Compare this with someone who listens to music like {friend_wrap.year}."
        except ObjectDoesNotExist:
            return render(request, 'wrap/analyze_wrap.html', {
                'error': "Invalid friend's Wrap ID provided."
            })

    try:
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        description = response.choices[0].message.content.strip()
    except Exception as e:
        description = f"Error generating analysis: {str(e)}"

    return render(request, 'wrap/analyze_wrap.html', {
        'description': description,
        'comparison_description': comparison_description,
        'wrap': wrap,
        'friend_wrap': friend_wrap
    })


'''
Creates a new Spotify Wrap for the logged-in user.

@param request: The HTTP request object.
@return: Redirect to the wraps list page or rendered HTML page for creating a wrap.
'''
def create(request):
    if request.method == 'POST':
        name = request.POST.get('wrap_name')
        theme = request.POST.get('theme')
        time_range = request.POST.get('time')

        # Ensure valid user is logged in
        user = request.user

        # Create the SpotifyWrap object
        wrap = SpotifyWrap.objects.create(
            user=user,
            wrap_id=uuid.uuid4(),
            name=name,
            theme=theme,
            time_range=time_range,
            year=2024,  # Example year, update accordingly
            data={},  # Assuming you're adding data here later
        )

        # Redirect to a page that shows the created wrap
        return redirect('view_wraps')

    return render(request, 'wrap/create_wrap.html')
