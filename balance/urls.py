from django.urls import path
from . import views

urlpatterns = [
    path('balance/', views.balance, name='balance'),
    path('stats', views.stats, name='stats'),
    path('scatter', views.scatter_view, name='scatter'),
]