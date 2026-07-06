# mikrotik_api/hotspot.py
import os
from dotenv import load_dotenv
from .client import get_mikrotik_connection
from librouteros.exceptions import TrapError

load_dotenv()
MIKROTIK_HOTSPOT_SERVER = os.getenv('MIKROTIK_HOTSPOT_SERVER', 'hotspot1')


def add_hotspot_user(room_number: str, password: str, uptime_limit: str):
    """
    Creates a new Hotspot user on the Mikrotik router.
    """
    # 1. Clean up any old instances of this room number to prevent API conflicts
    remove_hotspot_user(room_number)

    # 2. Add the new user using the Path.add() method
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/user')

            # Path.add() automatically formats the 'add' command and returns the new .id
            path.add(
                name=room_number,
                password=password,
                server=MIKROTIK_HOTSPOT_SERVER,
                **{'limit-uptime': uptime_limit}
            )
            print(f"[Mikrotik] Successfully added hotspot user: {room_number}")
        except TrapError as e:
            print(f"[Mikrotik] Failed to add user {room_number}: {e}")


# mikrotik_api/hotspot.py

def remove_hotspot_user(room_number: str):
    """
    Deletes a Hotspot user profile from the Mikrotik router.
    """
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/user')
            all_users = list(path("print"))

            # FIX: Cast both sides to string to prevent int vs str mismatch
            users = [user for user in all_users if str(user.get('name')) == str(room_number)]

            if not users:
                print(f"[Mikrotik] User {room_number} not found on router.")
                return

            for user in users:
                path.remove(user['.id'])
                print(f"[Mikrotik] Removed hotspot user profile: {room_number}")

        except TrapError as e:
            print(f"[Mikrotik] Failed to remove user {room_number}: {e}")


def drop_active_session(room_number: str):
    """
    Finds an actively connected device for this room and drops it.
    """
    with get_mikrotik_connection() as api:
        try:
            path = api.path('/ip/hotspot/active')

            # 1. Fetch all active sessions (Exactly like remove_hotspot_user)
            all_sessions = list(path("print"))

            # 2. Filter in Python, casting to string to prevent type mismatches
            active_sessions = [s for s in all_sessions if str(s.get('user')) == str(room_number)]

            if not active_sessions:
                print(f"[Mikrotik] No active session found for room {room_number}.")
                return

            # 3. Drop the sessions
            for session in active_sessions:
                # Since Path doesn't have a .drop() method, we use __call__
                # to execute the "drop" command. We wrap it in tuple() to
                # force the generator to execute the command immediately.
                tuple(path("remove", numbers=session['.id']))
                print(f"[Mikrotik] Dropped active session for room: {room_number}")

        except TrapError as e:
            print(f"[Mikrotik] Failed to drop session for {room_number}: {e}")