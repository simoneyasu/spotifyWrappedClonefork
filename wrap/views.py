from django.shortcuts import render, redirect, get_object_or_404
from functionality.views import get_User_Data, get_random_tracks
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
'''

dashboard of wraps. Shows buttons to create/view wraps

'''
@login_required
def dashboard(request):
    recent_wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'wrap/dashboard.html', {'user' : request.user, 'recent_wraps': recent_wraps})

'''

view your wrap

'''
def your_wrap(request, wrap_id):
    spotify_wrap = get_object_or_404(SpotifyWrap, wrap_id=wrap_id)

    access_token = request.session.get('access_token', None)
    if not access_token:
        return redirect('login')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # Get user data
    user_data = get_User_Data(access_token, "medium_term")
    random_tracks = get_random_tracks(headers)  # Call the method to get random tracks
    track_ids = [track['uri'].split(':')[-1] for track in random_tracks]  # Extract track IDs

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
        'track_ids': track_ids,
        'token': access_token
    }

    return render(request, 'wrap/your_wrap.html', context)

'''

View wrap

'''
@login_required
def view_wraps(request):
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')[:5]
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

    return render(request, 'wrap/view_wraps.html', {'wraps': wraps, 'no_wraps': no_wraps, 'share_urls': share_urls})

'''

shows the details of a wrap

'''
@login_required
def wrap_detail(request, wrap_id):
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    return render(request, 'wrap/wrap_detail.html', {'wrap': wrap})

'''

Gives user ability to delete a wrap

'''
@login_required
def delete_wrap(request, wrap_id):
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    wrap.delete()
    return redirect('view_wraps')

openai.api_key = settings.OPENAI_API_KEY


'''

Uses ChatGPT to analyze 

'''
@login_required
def analyze_wrap(request, wrap_id):
    wrap = SpotifyWrap.objects.filter(id=wrap_id, user=request.user).first()
    if not wrap:
        return render(request, 'wrap/analyze_wrap.html', {'error': "No Wrap data available for analysis."})

    prompt = f"Based on my music taste from {wrap.year}, describe how someone with similar taste might dress, act, or think."

    response = openai.ChatCompletion.create(
        model="o1-preview",
        messages=[{"role": "user", "content": prompt}]
    )

    description = response.choices[0].message['content'].strip()


    return render(request, 'wrap/analyze_wrap.html', {'description': description})

'''

Loads create wrap page

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
            name=name,
            theme=theme,
            time_range=time_range,
            year=2024,  # Example year, update accordingly
            data={},  # Assuming you're adding data here later
        )

        # Redirect to a page that shows the created wrap
        return redirect('dashboard')

    return render(request, 'wrap/create_wrap.html')

# LinkedIn Login View
def linkedin_login(request):
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={os.getenv('LINKEDIN_CLIENT_ID')}&"
        f"redirect_uri={os.getenv('LINKEDIN_REDIRECT_URI')}&"
        f"scope=w_member_social"
    )
    return redirect(auth_url)

# LinkedIn Callback View
def linkedin_callback(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'Authorization code not found'}, status=400)

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv('LINKEDIN_REDIRECT_URI'),
        "client_id": os.getenv('LINKEDIN_CLIENT_ID'),
        "client_secret": os.getenv('LINKEDIN_CLIENT_SECRET'),
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        request.session['linkedin_access_token'] = access_token  # Save the token in the session
        return JsonResponse({'access_token': access_token})
    else:
        return JsonResponse({'error': 'Failed to fetch access token'}, status=response.status_code)

def twitter_login(request):
    base_url = "https://twitter.com/i/oauth2/authorize"
    params = {
        "response_type": "code",
        "client_id": os.getenv("TWITTER_CLIENT_ID"),
        "redirect_uri": os.getenv("TWITTER_REDIRECT_URI"),
        "scope": "tweet.read tweet.write users.read offline.access",
        "state": "random_string_for_csrf_protection",
        "code_challenge": "challenge_value",  # PKCE 값
        "code_challenge_method": "plain",
    }
    request_url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
    return redirect(request_url)

def twitter_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No authorization code provided"}, status=400)

    token_url = "https://api.twitter.com/2/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("TWITTER_REDIRECT_URI"),
        "client_id": os.getenv("TWITTER_CLIENT_ID"),
        "client_secret": os.getenv("TWITTER_CLIENT_SECRET"),
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        request.session["twitter_access_token"] = tokens.get("access_token")
        request.session["twitter_refresh_token"] = tokens.get("refresh_token")
        return JsonResponse({"message": "Twitter authorization successful"})
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=response.status_code)

'''

Upload to Twitter

'''
@csrf_exempt
def upload_to_twitter(request):
    if request.method == "POST":
        image_data = request.POST.get("image")
        text = request.POST.get("text", "Check out my Spotify Wrapped!")

        if not image_data:
            return JsonResponse({"error": "No image data provided"}, status=400)

        try:
            # Decode Base64 image
            header, encoded = image_data.split(",", 1)
            image_binary = base64.b64decode(encoded)

            # OAuth1 인증
            auth = OAuth1(
                os.getenv("TWITTER_API_KEY"),
                os.getenv("TWITTER_API_SECRET"),
                os.getenv("TWITTER_ACCESS_TOKEN"),
                os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
            )

            # Step 1: Upload Media
            upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            files = {"media": image_binary}
            upload_response = requests.post(upload_url, auth=auth, files=files)

            if upload_response.status_code == 200:
                media_id = upload_response.json().get("media_id_string")

                # Step 2: Post Tweet
                post_url = "https://api.twitter.com/1.1/statuses/update.json"
                payload = {"status": text, "media_ids": media_id}
                post_response = requests.post(post_url, auth=auth, data=payload)

                if post_response.status_code == 200:
                    return JsonResponse({"message": "Tweet posted successfully!"})
                else:
                    return JsonResponse({"error": "Failed to post tweet"}, status=500)
            else:
                return JsonResponse({"error": "Failed to upload media"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

'''

Upload to LinkedIn

'''
@csrf_exempt
def upload_to_linkedin(request):
    if request.method == "POST":
        image_data = request.POST.get("image")
        text = request.POST.get("text", "Check out my Spotify Wrapped!")
        linkedin_access_token = request.session.get("linkedin_access_token")

        if not linkedin_access_token:
            return JsonResponse({"error": "LinkedIn access token is missing"}, status=401)

        # LinkedIn 사용자 ID 가져오기
        user_id = fetch_linkedin_user_id(linkedin_access_token)
        if not user_id:
            return JsonResponse({"error": "Failed to fetch LinkedIn user ID"}, status=400)

        try:
            # Decode Base64 image
            header, encoded = image_data.split(",", 1)
            image_binary = base64.b64decode(encoded)

            # Step 1: Initialize Upload
            initialize_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            headers = {
                "Authorization": f"Bearer {linkedin_access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{user_id}",
                }
            }
            init_response = requests.post(initialize_url, headers=headers, json=payload)

            if init_response.status_code != 201:
                return JsonResponse({"error": "Failed to initialize upload"}, status=400)

            upload_url = init_response.json()["value"]["uploadUrl"]
            asset = init_response.json()["value"]["asset"]

            # Step 2: Upload Image
            upload_response = requests.put(upload_url, headers=headers, data=image_binary)

            if upload_response.status_code != 201:
                return JsonResponse({"error": "Failed to upload image"}, status=400)

            # Step 3: Create Post
            post_url = "https://api.linkedin.com/v2/shares"
            post_payload = {
                "content": {
                    "contentEntities": [{"entityLocation": asset, "thumbnails": []}],
                    "title": text,
                },
                "owner": f"urn:li:person:{user_id}",
                "text": {"text": text},
            }
            post_response = requests.post(post_url, headers=headers, json=post_payload)

            if post_response.status_code == 201:
                return JsonResponse({"message": "Post shared successfully on LinkedIn!"})
            else:
                return JsonResponse({"error": "Failed to post on LinkedIn"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

def fetch_linkedin_user_id(access_token):
    url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"Failed to fetch LinkedIn user ID: {response.json()}")
        return None