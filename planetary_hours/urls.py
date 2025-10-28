from django.urls import path
from . import views

urlpatterns = [
    path("hours/", views.get_hours)
]