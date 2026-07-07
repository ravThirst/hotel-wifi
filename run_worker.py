# run_worker.py
import os
import time
import django

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_wifi_project.settings')
django.setup()

from django.core.management import call_command
from django.db import close_old_connections

def expiration_job():
    """Runs the expire_sessions command and cleans up DB connections."""
    print(f"[{time.strftime('%X')}] Running expiration job...")
    close_old_connections() # Prevents PostgreSQL timeout errors in long-running scripts
    call_command('expire_sessions')
    print(f"[{time.strftime('%X')}] Job complete. Sleeping for 60 seconds...\n")

print("=== Hotel WiFi Background Worker Started ===")
print("Press Ctrl+C to stop.")
print("==========================================\n")

# 2. Keep the script running forever using a simple sleep loop
try:
    while True:
        expiration_job()
        time.sleep(60) # Wait 60 seconds before running again
except KeyboardInterrupt:
    print("\nWorker stopped by user.")