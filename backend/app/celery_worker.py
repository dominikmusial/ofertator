from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery = Celery(
    "bot_sok_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks',
        'app.infrastructure.marketplaces.allegro.tasks',
        # 'app.infrastructure.marketplaces.decathlon.tasks', # Uncomment when tasks are implemented
    ]
)

# To add tasks for a new marketplace:
# 1. Create tasks in infrastructure/marketplaces/<marketplace>/tasks/
# 2. Add include path: 'app.infrastructure.marketplaces.<marketplace>.tasks'
# 3. Tasks auto-register via Celery discovery - no other changes needed
# Example: For Amazon marketplace, add 'app.infrastructure.marketplaces.amazon.tasks' to the include list above

celery.conf.update(
    task_track_started=True,
)

# Configure Celery Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    'check-and-update-prices-every-hour': {
        'task': 'check_and_update_prices_task',  # Fixed: matches registered task name
        'schedule': crontab(minute=0),  # Run at the start of every hour (:00)
    },
    'check-and-update-prices-daily': {
        'task': 'check_and_update_prices_daily',  # This one is correct
        'schedule': crontab(hour=0, minute=1),  # Run once a day at 00:01
    },
}

celery.conf.timezone = 'Europe/Warsaw'  # Adjust to your timezone 