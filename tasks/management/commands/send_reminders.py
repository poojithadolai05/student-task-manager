from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
from tasks.models import Task, UserProfile

class Command(BaseCommand):
    help = 'Send task reminders and overdue alerts'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        upcoming = now + timezone.timedelta(hours=24)

        for user in User.objects.all():
            email = user.email
            if not email:
                continue

            # ❗ Check user preference
            if not hasattr(user, 'userprofile') or not user.userprofile.email_reminders:
                continue

            # 🔔 Filter tasks
            upcoming_tasks = Task.objects.filter(
                user=user,
                deadline__lte=upcoming,
                deadline__gte=now,
                status='pending'
            )
            overdue_tasks = Task.objects.filter(
                user=user,
                deadline__lt=now,
                status='pending'
            )

            if not upcoming_tasks and not overdue_tasks:
                continue

            subject = '📌 Task Reminder & Overdue Alert'
            plain_message = f"Hello {user.username},\n\n"
            if upcoming_tasks:
                plain_message += "⏰ You have upcoming tasks:\n"
                for task in upcoming_tasks:
                    plain_message += f"• {task.title} — Due: {task.deadline.strftime('%Y-%m-%d %H:%M')}\n"
                plain_message += '\n'

            if overdue_tasks:
                plain_message += "⚠️ Overdue tasks:\n"
                for task in overdue_tasks:
                    plain_message += f"• {task.title} — Was Due: {task.deadline.strftime('%Y-%m-%d %H:%M')}\n"
                plain_message += '\n'

            plain_message += "📝 Login: http://127.0.0.1:8000/"

            # ✨ HTML version
            html_message = render_to_string('emails/task_reminder.html', {
                'user': user,
                'upcoming_tasks': upcoming_tasks,
                'overdue_tasks': overdue_tasks,
            })

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=html_message
            )

        self.stdout.write(self.style.SUCCESS('✅ Emails sent to users who opted in and have tasks.'))
