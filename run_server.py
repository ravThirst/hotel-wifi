# run_server.py
import os
import sys
from waitress import serve

# Ensure Django settings are loaded
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_wifi_project.settings')

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

if __name__ == '__main__':
    # Bind to 0.0.0.0 so it is accessible from OTHER computers on the hotel network
    host = '0.0.0.0'
    port = 8000

    print("=" * 50)
    print(f"Starting Hotel WiFi Production Server")
    print(f"Listening on http://{host}:{port}")
    print("Press Ctrl+C to stop the server.")
    print("=" * 50)

    # Start Waitress with 8 worker threads
    serve(application, host=host, port=port, threads=8)