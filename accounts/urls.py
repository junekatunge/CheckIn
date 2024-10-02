from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # Dashboard route to display all hosts and information
    path('', views.dashboard, name='dashboard'),

    # Meeting management routes
    path('meeting/', views.meeting_manager, name='meeting_manager'),  # Manage meetings (view or create)
    path('save_meeting/', views.save_meeting, name='save_meeting'),  # Save a new meeting

    # Profile management routes
    path('profile_manager/', views.profile_manager, name='profile_manager'),  # Add new host profile
    path('edit_profile/', views.edit_profile, name='save_profile'),  # Edit an existing host profile
    path('edit_delete/', views.edit_delete, name='edit_delete'),  # Edit or delete a host profile

    # Verification route for user authentication
    path('verification/', views.verify, name='verification'),  # Verify user credentials

    # Checkout route for visitor check-out process
    path('checkout/', views.checkout, name='checkout'),  # Handle visitor check-out

   
]
