from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import TutorDailyUsage


def reserve_daily_request(limit):
    """Reserve one UTC-day tutor request before contacting the provider."""
    if limit <= 0:
        return False

    with transaction.atomic():
        usage, _ = TutorDailyUsage.objects.select_for_update().get_or_create(
            date=timezone.localdate()
        )
        if usage.request_count >= limit:
            return False
        TutorDailyUsage.objects.filter(pk=usage.pk).update(
            request_count=F("request_count") + 1
        )
    return True
