from celery import shared_task
import time

@shared_task
def sample_task():
    time.sleep(2)
    return {"status": "Task completed successfully"}