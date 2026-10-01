from django.contrib.auth.models import User
from django.db import models
class Department(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(
        blank=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    def __str__(self):
        return self.title
class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name='students'
    )
    def __str__(self):
        return self.user.username