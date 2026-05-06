import os
import sys

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings


jobstores = {
    "default": RedisJobStore(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1),
}
executors = {
    "default": ThreadPoolExecutor(10),
}
job_defaults = {
    "coalesce": True,
    "max_instances": 3,
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
)

MANAGEMENT_COMMANDS_WITHOUT_SCHEDULER = {
    "check",
    "collectstatic",
    "createsuperuser",
    "makemigrations",
    "migrate",
    "shell",
}


def should_start_scheduler() -> bool:
    if os.getenv("START_WEB_SCHEDULER") != "1":
        return False

    if any(command in sys.argv for command in MANAGEMENT_COMMANDS_WITHOUT_SCHEDULER):
        return False

    if "runserver" in sys.argv and os.getenv("RUN_MAIN") != "true":
        return False

    return True


def start_scheduler() -> None:
    if should_start_scheduler() and not scheduler.running:
        scheduler.start()
