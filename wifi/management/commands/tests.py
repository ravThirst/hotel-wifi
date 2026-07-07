import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_wifi_project.settings")

import django
django.setup()

from django.utils import timezone
from datetime import timedelta
from rooms.models import Room
from wifi.models import WiFiSession

room = Room.objects.get(room_number="101")

# Create a session that expired 1 hour ago
WiFiSession.objects.create(
    room=room,
    password="EXPIRED123",
    expires_at=timezone.now() - timedelta(hours=1),
    is_active=True
)
exit()