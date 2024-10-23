from django.urls import path

from wrap import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wrap/', views.your_wrap, name='your_wrap'),
]