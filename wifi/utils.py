# wifi/utils.py
import secrets
import logging

from xhtml2pdf.files import pisaFileObject

from rooms.models import SystemSettings

import os
from io import BytesIO
from django.template.loader import get_template
from django.conf import settings
from xhtml2pdf import pisa

# Initialize logger for this module
logger = logging.getLogger('wifi.utils')


def generate_wifi_password(length: int = None) -> str:
    """
    Generates a secure, random WiFi password using the preset characters
    defined in the SystemSettings model.

    :param length: Optional custom length. If None, uses the default from DB.
    :return: A randomly generated string.
    """
    try:
        # 1. Fetch the global settings from the database (Singleton)
        settings = SystemSettings.load()

        # 2. Determine the length and allowed characters
        pwd_length = length if length else settings.default_password_length
        allowed_chars = settings.password_preset_chars

        # 3. Safety fallback in case the DB string was accidentally emptied
        if not allowed_chars:
            logger.warning("SystemSettings password_preset_chars is empty! Using fallback.")
            allowed_chars = "1234567890"

        if pwd_length <= 0:
            logger.warning(f"Invalid password length ({pwd_length}). Defaulting to 8.")
            pwd_length = 8

        # 4. Generate the password securely
        # secrets.choice() picks a random character from the allowed string
        password = ''.join(secrets.choice(allowed_chars) for _ in range(pwd_length))

        return password

    except Exception as e:
        logger.error(f"Failed to generate password: {e}")
        # Ultimate fallback so the app doesn't crash if the DB is unreachable
        return ''.join(secrets.choice("1234567890") for _ in range(8))


from datetime import timedelta

def format_mikrotik_uptime(td: timedelta) -> str:
    """
    Converts a Python timedelta into Mikrotik's time string format (e.g., '2d14h30m').
    """
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return "1m"  # Fallback to 1 minute if somehow 0 or negative

    weeks, rem = divmod(total_seconds, 604800)
    days, rem = divmod(rem, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if weeks: parts.append(f"{weeks}w")
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if seconds and not (weeks or days or hours or minutes):
        # Only add seconds if it's less than a minute, otherwise Mikrotik prefers minute rounding
        parts.append(f"{seconds}s")

    return "".join(parts) if parts else "1m"


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access static files.
    """
    from django.contrib.staticfiles import finders

    # If it's a static file (e.g., /static/logo.png)
    if uri.startswith(settings.STATIC_URL):
        path =  os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ''))
        pisaFileObject.getNamedFile = lambda self: path
        return path


    # If it's a media file (e.g., /media/uploads/image.jpg)
    elif uri.startswith(settings.MEDIA_URL):
        path =  os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
        pisaFileObject.getNamedFile = lambda self: path
        return path

    # Fallback to absolute path
    return uri


def render_to_pdf(template_src, context_dict={}):
    """
    Renders a Django template to a PDF byte stream.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()

    # Create the PDF. We use the link_callback to resolve static images.
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        encodind='UTF-8',
        link_callback=link_callback
    )

    if not pdf.err:
        return result.getvalue()
    return None


# wifi/utils.py
import re


def parse_mikrotik_time(time_str: str) -> int:
    """
    Parses a Mikrotik time string (e.g., '1d12h30m', '3h', '0s') into total seconds.
    """
    if not time_str or str(time_str) == '0s':
        return 0

    pattern = re.compile(r'(\d+)([wdhms])')
    matches = pattern.findall(str(time_str))

    total_seconds = 0
    for value, unit in matches:
        val = int(value)
        if unit == 'w':
            total_seconds += val * 604800
        elif unit == 'd':
            total_seconds += val * 86400
        elif unit == 'h':
            total_seconds += val * 3600
        elif unit == 'm':
            total_seconds += val * 60
        elif unit == 's':
            total_seconds += val

    return total_seconds