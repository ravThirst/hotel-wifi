import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_wifi_project.settings")

import django
django.setup()

from django.utils import timezone
from datetime import timedelta
from rooms.models import Room, SystemSettings
from wifi.models import WiFiSession
from wifi.utils import generate_wifi_password
from mikrotik_api.hotspot import add_hotspot_user, remove_hotspot_user



from django.core.management import call_command

# Ensure we have a test room (Room 101)
room, created = Room.objects.get_or_create(room_number="101", floor=1)
if created:
    print("Created test Room 101.")
else:
    print("Using existing Room 101.")

# Clear any old test sessions from the DB to start fresh
WiFiSession.objects.filter(room=room).delete()
remove_hotspot_user("101")
print("Cleared old DB sessions and Mikrotik users for Room 101.\n")

print("--- SCENARIO 1: FIRST GENERATION ---")

# 1. Generate Password & Calculate Expiration (Mirrors views.py)
password = generate_wifi_password()
timeout_hours = 24
expires_at = timezone.now() + timedelta(hours=timeout_hours)
uptime_limit = f"{timeout_hours}h"

print(f"Generated Password: {password}")

# 2. Push to Mikrotik
mikrotik_id = add_hotspot_user(
    room_number=str(room.room_number),
    password=password,
    uptime_limit=uptime_limit
)
print(f"Mikrotik returned ID: {mikrotik_id}")

# 3. Save to Database (Mirrors views.py)
WiFiSession.objects.create(
    room=room,
    password=password,
    mikrotik_user_id=mikrotik_id,
    expires_at=expires_at,
    is_active=True
)

# 4. Verify State
db_sessions = WiFiSession.objects.filter(room=room)
print(f"\n[DB STATE] Total sessions in DB for Room 101: {db_sessions.count()}")
print(f"[DB STATE] Active sessions: {db_sessions.filter(is_active=True).count()}")
print(">>> ACTION REQUIRED: Open your Mikrotik router (WinBox/WebFig) and check IP -> Hotspot -> Users. You should see user '101' with the password printed above!")
input("\nPress Enter to continue to Scenario 2...")