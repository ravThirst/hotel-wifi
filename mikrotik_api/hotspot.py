# mikrotik_api/hotspot.py
import os
import logging
from dotenv import load_dotenv
from .client import get_mikrotik_connection
from .exceptions import MikrotikConnectionError, MikrotikOperationError
from librouteros.exceptions import TrapError, ConnectionClosed

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
                return

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


def drop_active_session(room_number: str):
    """Finds an actively connected device for this room and removes it."""
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/active')
            all_sessions = list(path("print"))
            active_sessions = [s for s in all_sessions if str(s.get('user')) == str(room_number)]

            if not active_sessions:
                logger.info(f"No active session found for room {room_number}.")
                return

            for session in active_sessions:
                path.remove(session['.id'])
                logger.info(f"Dropped active session for room: {room_number}")

        except ConnectionClosed as e:
            logger.error(f"Router offline while dropping session for {room_number}: {e}")
            raise MikrotikConnectionError("Cannot connect to the Mikrotik router.")
        except TrapError as e:
            logger.error(f"Router rejected drop command for {room_number}: {e}")
            raise MikrotikOperationError(f"Router rejected the session drop. Detail: {e}")
        except Exception as e:
            logger.error(f"Exception {room_number}: {e}")