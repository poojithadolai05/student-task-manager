from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import  PasswordChangeForm
from django.contrib import messages
from django.utils.timezone import now
from .forms import CustomUserCreationForm
from django.core.mail import send_mail
from django.conf import settings
import csv
from .models import Task
from .forms import TaskForm
from django.utils import timezone
from .forms import EmailPreferenceForm
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField

# 📋 Display All Tasks
@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    now = timezone.now()

    # 🔍 Search
    query = request.GET.get('search', '')
    if query:
        tasks = tasks.filter(title__icontains=query)

    # 🔄 Filter by status
    status_filter = request.GET.get('filter', '')
    if status_filter in ['pending', 'completed']:
        tasks = tasks.filter(status=status_filter)

    # ⏳ Sorting
    sort = request.GET.get('sort', 'deadline')
    order = request.GET.get('order', 'asc')

    if sort == 'priority':
        priority_order = Case(
            When(priority='high', then=0),
            When(priority='medium', then=1),
            When(priority='low', then=2),
            default=3,
            output_field=IntegerField()
        )
        tasks = tasks.order_by(priority_order if order == 'asc' else priority_order.desc())
    else:
        sort_field = sort if sort in ['created_at', 'deadline'] else 'deadline'
        tasks = tasks.order_by(sort_field if order == 'asc' else f'-{sort_field}')

    # 📑 Pagination
    paginator = Paginator(tasks, 6)  # 6 tasks per page
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)

    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'search': query,
        'status_filter': status_filter,
        'sort': sort,
        'order': order,
        'now': timezone.now(),
    })

# ➕ Add a New Task
@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.status = 'pending'
            task.save()
            messages.success(request, "✅ Task added successfully!")
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form})


# ✏️ Edit Existing Task
@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "✏️ Task updated successfully!")
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {'form': form})


# ✔️ Mark Task as Completed
@login_required
def mark_completed(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.status = 'completed'
    task.save()
    messages.success(request, f"✔️ '{task.title}' marked as completed.")
    return redirect('task_list')


# ❌ Delete Task
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    messages.success(request, "🗑️ Task deleted successfully.")
    return redirect('task_list')

#register
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # ✅ Send confirmation email
            subject = '🎉 Welcome to Student Task Manager!'
            message = f'Hi {user.username},\n\nThanks for registering. You can now start managing your tasks efficiently.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]

            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            messages.success(request, "🎉 Registration successful! A confirmation email has been sent.")
            return redirect('task_list')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'tasks/register.html', {'form': form})

# 📤 Export Tasks as CSV
@login_required
def export_tasks_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks.csv"'

    writer = csv.writer(response)
    # ✅ Add 'Description' and 'Priority' columns
    writer.writerow(['Title', 'Description', 'Priority', 'Status', 'Created At', 'Deadline'])

    tasks = Task.objects.filter(user=request.user)
    for task in tasks:
        writer.writerow([
            task.title,
            task.description,
            task.priority,
            task.status,
            task.created_at.strftime('%Y-%m-%d %H:%M'),
            task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else ''
        ])

    return response


# 🧹 Delete User Account
@login_required
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()
    messages.success(request, "🧹 Your account has been deleted successfully.")
    return redirect('login')


# change password
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            # ✅ Send confirmation email
            send_mail(
                subject='🔐 Password Changed',
                message=f'Hi {user.username},\n\nYour password has been successfully changed.',
                from_email='dolaipoojitha05@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, "🔐 Password changed successfully!")
            return redirect('task_list')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'tasks/change_password.html', {'form': form})


# ⚙️ Account Settings View
@login_required
def account_settings(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = EmailPreferenceForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Preferences updated!")
            return redirect('account_settings')
    else:
        form = EmailPreferenceForm(instance=profile)

    return render(request, 'tasks/account_settings.html', {'form': form})


# 👤 User Profile Summary
@login_required
def profile(request):
    user = request.user
    tasks = Task.objects.filter(user=user)

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    pending_tasks = tasks.filter(status='pending').count()
    progress = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

    upcoming_tasks = tasks.filter(status='pending', deadline__gte=now()).order_by('deadline')[:3]

    return render(request, 'tasks/profile.html', {
        'user': user,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'progress': progress,
        'upcoming_tasks': upcoming_tasks,
    })

def custom_logout(request):
    logout(request)
    messages.success(request, "🚪 You have been logged out successfully.")
    return redirect('login')
