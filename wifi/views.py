import logging

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
def handle_session(request, room_id):
    """
    Unified view to handle both Generating a new password and Extending an existing one.
    """
    if request.method != 'POST':
        return redirect('dashboard')

    room = get_object_or_404(Room, id=room_id, is_active=True)
    action = request.POST.get('action')  # 'generate' or 'extend'
    date_str = request.POST.get('checkout_date')

    # 1. Validate Date
    if not date_str:
        messages.error(request, "Пожалуйста введите период действия.")
        return redirect('dashboard')

    try:
        # Combine date with static 13:00 time
        naive_dt = datetime.strptime(f"{date_str} 13:00", "%Y-%m-%d %H:%M")
        target_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
    except ValueError:
        messages.error(request, "Неверный формат даты.")
        return redirect('dashboard')

    now = timezone.now()
    if target_dt <= now:
        messages.error(request, "Дата не должна быть раньше текущей.")
        return redirect('dashboard')

    # 2. Route based on which button was clicked
    if action == 'generate':
        # --- GENERATE LOGIC ---
        password = generate_wifi_password()
        time_difference = target_dt - now
        uptime_limit = format_mikrotik_uptime(time_difference)

        try:
            mikrotik_id = add_hotspot_user(
                room_number=str(room.room_number),
                password=password,
                uptime_limit=uptime_limit
            )
        except (MikrotikConnectionError, MikrotikOperationError) as e:
            messages.error(request, f"Router Error: {e}. Password was NOT saved.")
            return redirect('dashboard')

        WiFiSession.objects.filter(room=room, is_active=True).update(is_active=False)
        WiFiSession.objects.create(
            room=room, password=password, mikrotik_user_id=mikrotik_id,
            expires_at=target_dt, created_by=request.user, is_active=True
        )
        messages.success(
            request,
            f"WiFi активирован для номера {room.room_number} до {timezone.localtime(target_dt).strftime('%Y-%m-%d %H:%M')}! Пароль: {password}"
        )

    elif action == 'extend':
        # --- EXTEND LOGIC ---
        session = room.current_session
        if not session or not session.is_active or session.is_expired:
            messages.error(request, "Нет активный сессий для продления.")
            return redirect('dashboard')

        if target_dt <= session.expires_at:
            messages.warning(request, "Дата продления не должна быть раньше текущей даты действия.")
            return redirect('dashboard')

        # Calculate how many seconds to ADD to their current session
        time_difference = target_dt - now
        additional_seconds = int(time_difference.total_seconds())

        try:
            update_hotspot_user_limit(str(room.room_number), additional_seconds)
        except (MikrotikConnectionError, MikrotikOperationError) as e:
            messages.error(request, f"Router Error: {e}")
            return redirect('dashboard')

        session.expires_at = target_dt
        session.save()
        messages.success(
            request,
            f"Продлен WiFi для номера {room.room_number} до {timezone.localtime(target_dt).strftime('%Y-%m-%d %H:%M')}. Пароль останется без изменения."
        )

    else:
        messages.error(request, "Неверное действие.")

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
        messages.error(request, "Нет активный сессий для печати.")
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

    return HttpResponse("Ошибка генерации PDF. Please check server logs.", status=400)