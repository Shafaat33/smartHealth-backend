from prometheus_client import Counter

appointments_booked_total = Counter(
    "appointments_booked_total",
    "Appointments booked after Temporal hold started",
)
notifications_delivered_total = Counter(
    "notifications_delivered_total",
    "Notification rows written by Celery",
)
notifications_failed_total = Counter(
    "notifications_failed_total",
    "Celery send_notification failures",
)
