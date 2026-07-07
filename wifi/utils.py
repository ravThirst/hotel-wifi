# wifi/utils.py
import secrets
import logging
from rooms.models import SystemSettings

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


def format_mikrotik_uptime(total_seconds: int) -> str:
    """
    Converts total seconds into Mikrotik's time interval format (e.g., '1d12h30m').
    """
    if total_seconds <= 0:
        return "1m"  # Fallback to 1 minute if somehow 0 or negative

    weeks, rem = divmod(total_seconds, 604800)
    days, rem = divmod(rem, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if weeks > 0: parts.append(f"{weeks}w")
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")

    # If the duration is less than a minute, Mikrotik still needs a valid string
    if not parts and seconds > 0:
        parts.append(f"{seconds}s")

    return "".join(parts) if parts else "1m"