from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Course
@login_required
def profile(request):
    return render(request, 'profile.html')
@login_required
def course_list(request):
    courses = Course.objects.select_related('department').all()
    return render(
    request,
    'course_list.html',
{
        'courses': courses,
        }
    )