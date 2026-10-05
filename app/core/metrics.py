from prometheus_client import Counter, Histogram

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

ai_questions_total = Counter(
    "ai_questions_total",
    "Assistant chat requests completed",
    labelnames=("intent", "status"),
)
ai_response_seconds = Histogram(
    "ai_response_seconds",
    "Assistant end-to-end response time",
    labelnames=("intent",),
    buckets=(0.25, 0.5, 1, 2, 5, 10, 30, 60),
)
ai_retrieval_empty_total = Counter(
    "ai_retrieval_empty_total",
    "Knowledge retrieval returned no chunks above threshold",
)
ai_llm_errors_total = Counter(
    "ai_llm_errors_total",
    "Assistant LLM or pipeline failures",
    labelnames=("stage",),
)
ai_suggestions_total = Counter(
    "ai_suggestions_total",
    "Booking suggestions emitted to patients",
)
