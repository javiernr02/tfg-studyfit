from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-study-activity/', views.create_study_activity, name='create_study_activity'),
    path('create-subject/', views.create_subject, name='create_subject'),
    path('create-sport-activity/', views.create_sport_activity, name='create_sport_activity'),
    path('subject/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
]