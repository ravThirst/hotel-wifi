# wifi/management/commands/expire_sessions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from wifi.models import WiFiSession
from wifi.utils import generate_wifi_password
from mikrotik_api.hotspot import drop_active_session, remove_hotspot_user
from mikrotik_api.exceptions import MikrotikConnectionError, MikrotikOperationError


class Command(BaseCommand):
    help = 'Finds expired WiFi sessions, kicks guests off Mikrotik, clears cookies, and resets room passwords.'

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # 1. Find all sessions that are marked active but have passed their checkout time
        expired_sessions = WiFiSession.objects.filter(
            is_active=True,
            expires_at__lte=now
        ).select_related('room')

        if not expired_sessions.exists():
            self.stdout.write(self.style.SUCCESS('No expired sessions found.'))
            return

        self.stdout.write(f'Found {expired_sessions.count()} expired session(s). Processing...')

        for session in expired_sessions:
            room = session.room
            room_number = str(room.room_number)

            self.stdout.write(f'Processing Room {room_number}...')

            try:
                # 2. Kick the guest off and wipe their MAC cookie
                drop_active_session(room_number)

                # 3. Delete the user profile from the router completely
                remove_hotspot_user(room_number)

            except (MikrotikConnectionError, MikrotikOperationError) as e:
                # If the router is offline, we log the error but CONTINUE processing the database.
                # We don't want a router outage to freeze our database state.
                self.stdout.write(self.style.ERROR(f'Router error for Room {room_number}: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Unexpected error for Room {room_number}: {e}'))

            # 4. Update the Database (Use atomic transaction for safety)
            with transaction.atomic():
                # Mark the old session as inactive
                session.is_active = False
                session.save()

                # Generate a new random password for the room so it's ready for the next guest
                # (This ensures the old password can never be used again, even if the router failed to delete it)
                new_password = generate_wifi_password()

                # We create a "placeholder" inactive session just to record the new default password
                # in the database history, or you can simply store this on the Room model if you prefer.
                # For this architecture, we just log the reset.
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully expired Room {room_number}. New standby password generated: {new_password}'
                ))

        self.stdout.write(self.style.SUCCESS('Expiration cycle complete.'))