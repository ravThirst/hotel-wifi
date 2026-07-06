from django.shortcuts import render

# wifi/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from rooms.models import Room
from .models import WiFiSession
from .utils import generate_wifi_password
from mikrotik_api.hotspot import add_hotspot_user
from mikrotik_api.exceptions import MikrotikConnectionError, MikrotikOperationError


@login_required
def dashboard(request):
    """
    Main dashboard for hotel staff to view rooms and their WiFi status.
    """
    query = request.GET.get('q', '')
    rooms = Room.objects.filter(is_active=True)

    # Filter by room number if a search query is present
    if query:
        rooms = rooms.filter(room_number__icontains=query)

    context = {
        'rooms': rooms,
        'query': query,
    }
    # Note: We will create 'wifi/dashboard.html' in Phase 5
    return render(request, 'wifi/dashboard.html', context)


@login_required
def generate_session(request, room_id):
    """
    Handles the POST request to generate a new WiFi password,
    push it to Mikrotik, and save it to the database.
    """
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id, is_active=True)

        # 1. Get timeout from form (in hours), default to 24
        try:
            timeout_hours = int(request.POST.get('timeout', 24))
        except ValueError:
            timeout_hours = 24

        uptime_limit = f"{timeout_hours}h"

        # 2. Generate the password
        password = generate_wifi_password()

        # 3. Calculate expiration time
        expires_at = timezone.now() + timedelta(hours=timeout_hours)

        # 4. Push to Mikrotik Router
        try:
            # We pass the room number as a string to avoid int/str mismatch in librouteros
            mikrotik_id = add_hotspot_user(
                room_number=str(room.room_number),
                password=password,
                uptime_limit=uptime_limit
            )
        except (MikrotikConnectionError, MikrotikOperationError) as e:
            messages.error(request, f"Router Error: {e}. Password was NOT saved to database.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            return redirect('dashboard')

        # 5. Save to Database
        # First, deactivate any lingering active sessions for this room
        WiFiSession.objects.filter(room=room, is_active=True).update(is_active=False)

        # Create the new session
        WiFiSession.objects.create(
            room=room,
            password=password,
            mikrotik_user_id=mikrotik_id,  # Save the router's internal ID!
            expires_at=expires_at,
            created_by=request.user,
            is_active=True
        )

        messages.success(request, f"WiFi activated for Room {room.room_number}! Password: {password}")
        return redirect('dashboard')

    # If someone tries to access this via GET, redirect them back to dashboard
    return redirect('dashboard')