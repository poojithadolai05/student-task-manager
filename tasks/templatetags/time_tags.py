from django import template
from django.utils import timezone
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def deadline_status(deadline):
    now = timezone.now()

    if not deadline:
        return ""

    if deadline > now:
        return f"⏳ {timesince(now, deadline)} left"
    else:
        return f"❌ Overdue by {timesince(deadline, now)}"
