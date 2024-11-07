from django.urls import path

from wrap import views
from register import views as register_views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wrap/', views.view_wraps, name='view_wraps'),
    path('wrap/<int:wrap_id>/', views.wrap_detail, name='wrap_detail'),
    path('wrap/<int:wrap_id>/delete/', views.delete_wrap, name='delete_wrap'),
    path('wrap/<int:wrap_id>/analyze/', views.analyze_wrap, name='analyze_wrap'),
    path('callback/', register_views.spotify_callback, name='spotify_callback'),
]