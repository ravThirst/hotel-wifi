# mikrotik_api/hotspot.py
import os
import logging
from dotenv import load_dotenv
from .client import get_mikrotik_connection
from .exceptions import MikrotikConnectionError, MikrotikOperationError
from librouteros.exceptions import TrapError, ConnectionClosed
from wifi.utils import format_mikrotik_uptime, parse_mikrotik_time # Add these imports
from datetime import timedelta

# Initialize the logger for this module
logger = logging.getLogger('mikrotik_api')

load_dotenv()
MIKROTIK_HOTSPOT_SERVER = os.getenv('MIKROTIK_HOTSPOT_SERVER', 'hotspot1')


# mikrotik_api/hotspot.py

def add_hotspot_user(room_number: str, password: str, uptime_limit: str) -> str:
    """Creates a new Hotspot user on the Mikrotik router and returns its internal ID."""
    remove_hotspot_user(room_number)

    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/user')

            # path.add() automatically returns the new internal .id (e.g., '*1A')
            mikrotik_id = path.add(
                name=room_number,
                password=password,
                server=MIKROTIK_HOTSPOT_SERVER,
                **{'limit-uptime': uptime_limit}
            )
            logger.info(f"Successfully added hotspot user: {room_number} (ID: {mikrotik_id})")
            return mikrotik_id

        except ConnectionError as e:
            logger.error(f"Router offline while adding {room_number}: {e}")
            raise MikrotikConnectionError("Cannot connect to the Mikrotik router.")
        except TrapError as e:
            logger.error(f"Router rejected add command for {room_number}: {e}")
            raise MikrotikOperationError(f"Router rejected the new password. Detail: {e}")
        except Exception as e:
            logger.error(f"Exception {room_number}: {e}")


def remove_hotspot_user(room_number: str):
    """Deletes a Hotspot user profile from the Mikrotik router."""
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/user')
            all_users = list(path("print"))
            users = [user for user in all_users if str(user.get('name')) == str(room_number)]

            if not users:
                logger.info(f"User {room_number} not found on router during cleanup.")

            else:
                for user in users:
                    path.remove(user['.id'])
                    logger.info(f"Removed hotspot user profile: {room_number}")

        except ConnectionClosed as e:
            logger.error(f"Router offline while removing {room_number}: {e}")
            raise MikrotikConnectionError("Cannot connect to the Mikrotik router.")
        except TrapError as e:
            logger.error(f"Router rejected remove command for {room_number}: {e}")
            raise MikrotikOperationError(f"Router rejected the removal. Detail: {e}")
        except Exception as e:
            logger.error(f"Exception {room_number}: {e}")

        drop_active_session(room_number)


# mikrotik_api/hotspot.py

def clear_hotspot_cookies(room_number: str):
    """
    Removes hotspot cookies for the given user.
    This prevents the guest's device from automatically reconnecting
    and bypassing the captive portal login page.
    """
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/cookie')
            all_cookies = list(path("print"))

            # Filter cookies by user (casting to string to avoid type issues)
            user_cookies = [c for c in all_cookies if str(c.get('user')) == str(room_number)]

            if not user_cookies:
                logger.info(f"No cookies found for room {room_number}.")
                return

            for cookie in user_cookies:
                path.remove(cookie['.id'])
                logger.info(f"Cleared hotspot cookie for room: {room_number}")

        except ConnectionError as e:
            logger.error(f"Router offline while clearing cookies for {room_number}: {e}")
            raise MikrotikConnectionError("Cannot connect to the Mikrotik router.")
        except TrapError as e:
            logger.error(f"Router rejected cookie clear command for {room_number}: {e}")
            raise MikrotikOperationError(f"Router rejected the cookie clear. Detail: {e}")


def drop_active_session(room_number: str):
    """
    Completely wipes a room's hotspot state:
    1. Removes the active connection (kills current internet).
    2. Clears the hotspot cookie (forces captive portal on reconnect).
    """
    with get_mikrotik_connection() as api:
        try:
            # 1. Drop Active Sessions
            active_path = api.path('/ip/hotspot/active')
            all_sessions = list(active_path("print"))
            active_sessions = [s for s in all_sessions if str(s.get('user')) == str(room_number)]

            if active_sessions:
                for session in active_sessions:
                    active_path.remove(session['.id'])
                    logger.info(f"Dropped active session for room: {room_number}")
            else:
                logger.info(f"No active session found for room {room_number}.")

        except ConnectionError as e:
            logger.error(f"Router offline while dropping session for {room_number}: {e}")
            raise MikrotikConnectionError("Cannot connect to the Mikrotik router.")
        except TrapError as e:
            logger.error(f"Router rejected drop command for {room_number}: {e}")
            raise MikrotikOperationError(f"Router rejected the session drop. Detail: {e}")
        except Exception as e:
            logger.error(f"Exception {room_number}: {e}")
            raise MikrotikOperationError(f"Exception. Detail: {e}")

    # 2. Clear Cookies (Called after to ensure active session is dead first)
    clear_hotspot_cookies(room_number)


def update_hotspot_user_limit(room_number: str, additional_seconds: int):
    """
    Extends the limit-uptime of an existing Hotspot user without changing the password.
    Adds the additional_seconds to the user's CURRENT uptime to prevent immediate disconnection.
    """
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/user')
            all_users = list(path("print"))
            users = [user for user in all_users if str(user.get('name')) == str(room_number)]

            if not users:
                logger.warning(f"User {room_number} not found on router for limit update.")
                raise MikrotikOperationError(f"User {room_number} not found on router.")

            user = users[0]

            # 1. Get how long they have already been connected
            current_uptime_str = user.get('uptime', '0s')
            current_uptime_sec = parse_mikrotik_time(current_uptime_str)

            # 2. Calculate the new TOTAL limit (Current Uptime + Additional Time)
            new_total_seconds = current_uptime_sec + additional_seconds
            new_limit_str = format_mikrotik_uptime(timedelta(seconds=new_total_seconds))

            # 3. Update the router using the Path.update() method (maps to 'set' command)
            path.update(**{".id": user['.id'], "limit-uptime": new_limit_str})
            logger.info(f"Extended limit-uptime for {room_number} to {new_limit_str}")

        except ConnectionError as e:
            logger.error(f"Router offline while updating limit for {room_number}: {e}")
            raise MikrotikConnectionError("Cannot connect to the Mikrotik router.")
        except TrapError as e:
            logger.error(f"Router rejected update command for {room_number}: {e}")
            raise MikrotikOperationError(f"Router rejected the update. Detail: {e}")
        except Exception as e:
            logger.error(f"Exception {room_number}: {e}")
            raise MikrotikOperationError(f"Exception. Detail: {e}")