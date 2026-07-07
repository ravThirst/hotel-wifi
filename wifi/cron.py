# wifi/cron.py
from django.core.management import call_command
import logging

logger = logging.getLogger('mikrotik_api')

def expire_sessions_job():
    """
    Wrapper function for django-crontab to execute the expire_sessions management command.
    """
    try:
        logger.info("Cron job triggered: Running expire_sessions...")
        call_command('expire_sessions')
    except Exception as e:
        logger.error(f"Cron job failed with error: {e}")