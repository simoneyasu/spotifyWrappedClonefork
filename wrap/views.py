from django.shortcuts import render, redirect, get_object_or_404

from functionality.views import get_User_Data
import openai
from django.conf import settings
from django.contrib.auth.decorators import login_required
from register.models import SpotifyWrap

def dashboard(request):
    return render(request, 'wrap/dashboard.html')


def your_wrap(request):
    access_token = request.session.get('access_token', None)
    if not access_token:
        return redirect('login')

    # Get user data
    user_data = get_User_Data(access_token)

    # Pass user data to the template
    return render(request, 'wrap/your_wrap.html', user_data)

@login_required
def view_wraps(request):
    wraps = SpotifyWrap.objects.filter(user=request.user).order_by('-year')
    no_wraps = not wraps.exists()
    return render(request, 'wrap/view_wraps.html', {'wraps': wraps, 'no_wraps': no_wraps})

@login_required
def wrap_detail(request, wrap_id):
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    return render(request, 'wrap/wrap_detail.html', {'wrap': wrap})

@login_required
def delete_wrap(request, wrap_id):
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    wrap.delete()
    return redirect('view_wraps')

openai.api_key = settings.OPENAI_API_KEY

@login_required
def analyze_wrap(request, wrap_id):
    wrap = SpotifyWrap.objects.filter(id=wrap_id, user=request.user).first()
    if not wrap:
        return render(request, 'wrap/analyze_wrap.html', {'error': "No Wrap data available for analysis."})

    prompt = f"Describe the characteristics of people who listen to {wrap.year} Wrap."

    response = openai.ChatCompletion.create(
        model="o1-preview",
        messages=[{"role": "user", "content": prompt}]
    )

    description = response.choices[0].message['content'].strip()

    return render(request, 'wrap/analyze_wrap.html', {'description': description})