# mikrotik_api/client.py
import os
from contextlib import contextmanager
from librouteros import connect
from librouteros.exceptions import TrapError, ConnectionClosed, MultiTrapError
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Fetch Mikrotik credentials
MIKROTIK_IP = os.getenv('MIKROTIK_IP', '192.168.88.1')
MIKROTIK_USER = os.getenv('MIKROTIK_API_USER', 'admin')
MIKROTIK_PASS = os.getenv('MIKROTIK_API_PASSWORD', '')
MIKROTIK_PORT = int(os.getenv('MIKROTIK_PORT', 8728))


@contextmanager
def get_mikrotik_connection():
    """
    Context manager to safely open and close Mikrotik API connections.

    Usage:
        with get_mikrotik_connection() as api:
            api.path('/ip/hotspot/user').add(name='101', password='abc')
    """
    api = None
    try:
        # Open the connection to the Mikrotik router
        api = connect(
            username=MIKROTIK_USER,
            password=MIKROTIK_PASS,
            host=MIKROTIK_IP,
            port=MIKROTIK_PORT,
            timeout=10  # Timeout in seconds
        )
        yield api  # Hand the connection to the code block using this context manager

    except ConnectionClosed as e:
        print(f"[Mikrotik Error] Could not connect to router at {MIKROTIK_IP}:{MIKROTIK_PORT} - {e}")
        raise  # Re-raise the error so Django views can catch it and show a user-friendly message
    except (TrapError, MultiTrapError) as e:
        print(f"[Mikrotik Error] RouterOS rejected the command: {e}")
        raise
    except Exception as e:
        print(f"[Mikrotik Error] Unexpected error: {e}")
        raise
    finally:
        # ALWAYS close the connection, even if an error occurred
        if api is not None:
            try:
                api.close()
            except Exception:
                pass  # Ignore errors during closure