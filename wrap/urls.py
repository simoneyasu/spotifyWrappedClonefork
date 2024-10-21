from django.urls import path

from wrap import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]