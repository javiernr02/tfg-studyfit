from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    path('create-study-activity/', views.create_study_activity, name='create_study_activity'),
    path('cancel-study-activity/', views.cancel_study_activity, name='cancel_study_activity'),
    
    path('create-subject/', views.create_subject, name='create_subject'),
    path('subject/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    
    path('create-live-study-activity/', views.create_live_study_activity, name='create_live_study_activity'),
    path('cancel-live-study-activity/', views.cancel_live_study_activity, name='cancel_live_study_activity'),
    
    path('create-sport-activity/', views.create_sport_activity, name='create_sport_activity'),
    path('cancel-sport-activity/', views.cancel_sport_activity, name='cancel_sport_activity'),
    
    path('create-live-sport-activity/', views.create_live_sport_activity, name='create_live_sport_activity'),
    path('cancel-live-sport-activity/', views.cancel_live_sport_activity, name='cancel_live_sport_activity'),
    
    path('activity-history/', views.activity_history, name='activity_history'),
    path('activity/<int:activity_id>/edit/', views.edit_activity, name='edit_activity'),
    path('activity/<int:activity_id>/delete/', views.delete_activity, name='delete_activity'),
]