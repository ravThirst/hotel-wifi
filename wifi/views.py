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
from mikrotik_api.hotspot import add_hotspot_user, update_hotspot_user_limit
from mikrotik_api.exceptions import MikrotikConnectionError, MikrotikOperationError

from django.http import HttpResponse
from rooms.models import SystemSettings
from .utils import render_to_pdf # Make sure to import this!

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

        # 1. Get Date from form (Time is hardcoded to 13:00)
        date_str = request.POST.get('checkout_date')

        if not date_str:
            messages.error(request, "Please provide a checkout date.")
            return redirect('dashboard')

        try:
            # Combine date string with static 13:00 time
            naive_dt = datetime.strptime(f"{date_str} 13:00", "%Y-%m-%d %H:%M")
            checkout_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
        except ValueError:
            messages.error(request, "Invalid date format.")
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


# wifi/views.py
import os
import base64
from django.contrib.staticfiles import finders


@login_required
def print_ticket(request, room_id):
    """
    Generates and returns a PDF ticket for the room's active WiFi session.
    """
    room = get_object_or_404(Room, id=room_id)
    session = room.current_session

    if not session or not session.is_active or session.is_expired:
        messages.error(request, "No active WiFi session to print for this room.")
        return redirect('dashboard')

    # --- BULLETPROOF LOGO HANDLING ---
    logo_base64 = ""
    # Find the logo in your static folder
    logo_path = finders.find('logo.png')
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            # Convert image to Base64 string so xhtml2pdf can render it natively
            logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    context = {
        'room': room,
        'session': session,
        'ssid': SystemSettings.load().wifi_ssid,
        'logo_base64': logo_base64,  # Pass the Base64 string to the template
    }

    pdf = render_to_pdf('wifi/ticket.html', context)

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"WiFi_Ticket_Room_{room.room_number}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    return HttpResponse("Error generating PDF. Please check server logs.", status=400)


@login_required
def extend_session(request, room_id):
    """
    Extends the checkout time of an active session WITHOUT changing the password.
    """
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id, is_active=True)
        session = room.current_session

        if not session or not session.is_active or session.is_expired:
            messages.error(request, "No active session to extend.")
            return redirect('dashboard')

        date_str = request.POST.get('new_checkout_date')
        if not date_str:
            messages.error(request, "Please provide a new checkout date.")
            return redirect('dashboard')

        try:
            naive_dt = datetime.strptime(f"{date_str} 13:00", "%Y-%m-%d %H:%M")
            new_checkout_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('dashboard')

        now = timezone.now()
        if new_checkout_dt <= now:
            messages.error(request, "New checkout time must be in the future.")
            return redirect('dashboard')

        if new_checkout_dt <= session.expires_at:
            messages.warning(request, "New checkout date must be later than the current one.")
            return redirect('dashboard')

        # Calculate how many seconds to ADD to their current session
        time_difference = new_checkout_dt - now
        additional_seconds = int(time_difference.total_seconds())

        try:
            update_hotspot_user_limit(str(room.room_number), additional_seconds)
        except (MikrotikConnectionError, MikrotikOperationError) as e:
            messages.error(request, f"Router Error: {e}")
            return redirect('dashboard')

        # Update the database
        session.expires_at = new_checkout_dt
        session.save()

        messages.success(
            request,
            f"Extended WiFi for Room {room.room_number} until {timezone.localtime(new_checkout_dt).strftime('%Y-%m-%d %H:%M')}. Password remains the same."
        )
        return redirect('dashboard')

    return redirect('dashboard')