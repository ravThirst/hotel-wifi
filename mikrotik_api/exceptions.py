# mikrotik_api/exceptions.py

class MikrotikConnectionError(Exception):
    """Raised when the Django app cannot connect to the Mikrotik router."""
    pass

class MikrotikOperationError(Exception):
    """Raised when the Mikrotik router rejects a command (TrapError)."""
    pass