from celery import Celery
from app.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL
)

# Set Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="generate_ai_coach_insights")
def generate_ai_coach_insights(user_id: str):
    """
    Celery task running in a separate worker container to handle heavy
    background processing (e.g. calculating financial insights or reports).
    """
    print(f"[Celery Worker] Generating coach insights task triggered for user: {user_id}")
    # In future development phases, this will write results directly to a Cache/DB.
    return f"Completed insights generation for user {user_id}"
