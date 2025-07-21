from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from tasks import views as task_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='tasks/login.html'), name='login'),
    path('logout/', task_views.custom_logout, name='logout'),
]
