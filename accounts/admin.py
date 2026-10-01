from django.contrib import admin
from .models import Course, Department, StudentProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'department')
    list_filter = ('department',)
    search_fields = ('title',)
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department')
    list_filter = ('department',)
    search_fields = ('user__username',)
    filter_horizontal = ('courses',)