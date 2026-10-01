from django.urls import path
from . import views
urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('courses/', views.course_list, name='course_list'),
]