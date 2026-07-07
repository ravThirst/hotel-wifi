from django.shortcuts import render

# wifi/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from datetime import datetime

from rooms.models import Room
from .models import WiFiSession
from .utils import generate_wifi_password, format_mikrotik_uptime
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
    Handles the POST request to generate a new WiFi password based on exact checkout datetime.
    """
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id, is_active=True)

        # 1. Get Date and Time from form
        date_str = request.POST.get('checkout_date')
        time_str = request.POST.get('checkout_time')

        if not date_str or not time_str:
            messages.error(request, "Please provide both checkout date and time.")
            return redirect('dashboard')

        try:
            # 2. Combine strings into a naive datetime object
            naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            # 3. Make it timezone-aware using the server's configured TIME_ZONE
            checkout_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())

        except ValueError:
            messages.error(request, "Invalid date or time format.")
            return redirect('dashboard')

        # 4. Validate that checkout is in the future
        now = timezone.now()
        if checkout_dt <= now:
            messages.error(request, "Checkout time must be in the future.")
            return redirect('dashboard')

        # 5. Calculate exact time difference and format for Mikrotik
        time_difference = checkout_dt - now
        uptime_limit = format_mikrotik_uptime(time_difference)

        # 6. Generate the password
        password = generate_wifi_password()

        # 7. Push to Mikrotik Router
        try:
            mikrotik_id = add_hotspot_user(
                room_number=str(room.room_number),
                password=password,
                uptime_limit=uptime_limit
            )
        except (MikrotikConnectionError, MikrotikOperationError) as e:
            messages.error(request, f"Router Error: {e}. Password was NOT saved.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            return redirect('dashboard')

        # 8. Save to Database
        # Deactivate old sessions
        WiFiSession.objects.filter(room=room, is_active=True).update(is_active=False)

        # Create new session (expires_at now holds the exact checkout datetime!)
        WiFiSession.objects.create(
            room=room,
            password=password,
            mikrotik_user_id=mikrotik_id,
            expires_at=checkout_dt,  # Storing the exact checkout datetime
            created_by=request.user,
            is_active=True
        )

        messages.success(
            request,
            f"WiFi activated for Room {room.room_number} until {timezone.localtime(checkout_dt).strftime('%Y-%m-%d %H:%M')}! Password: {password}"
        )
        return redirect('dashboard')

    return redirect('dashboard')