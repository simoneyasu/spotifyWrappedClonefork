import uuid

from django.shortcuts import render, redirect, get_object_or_404

from functionality.views import get_User_Data
import openai
from django.conf import settings
from django.contrib.auth.decorators import login_required
from register.models import SpotifyWrap

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

    time_range_mapping = {
        'small': 'short_term',
        'medium': 'medium_term',
        'large': 'long_term'
    }

    term = time_range_mapping.get(spotify_wrap.time_range)

    user_data = get_User_Data(access_token, term)

    context = {
        'user_data': user_data,
        'spotify_wrap': spotify_wrap
    }

    return render(request, 'wrap/your_wrap.html', context)

'''

view your wrap

'''
@login_required
def view_wraps(request):
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-created_at')[:5]
    no_wraps = wraps.count() == 0
    return render(request, 'wrap/view_wraps.html', {'wraps': wraps, 'user': request.user, 'no_wraps' : no_wraps})

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

