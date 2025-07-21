from django.contrib import admin
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at', 'deadline')
    list_filter = ('status', 'user')
    search_fields = ('title',)

admin.site.register(Task, TaskAdmin)
