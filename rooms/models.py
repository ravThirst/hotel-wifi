from django.db import models

class Room(models.Model):
    """
    Represents a physical hotel room.
    """
    room_number = models.CharField(
        max_length=10,
        unique=True,
        help_text="e.g., '101', '204B', 'Penthouse'"
    )
    floor = models.IntegerField(
        help_text="Floor number where the room is located."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to disable WiFi management for this room (e.g., out of order)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['floor', 'room_number']
        verbose_name = "Hotel Room"
        verbose_name_plural = "Hotel Rooms"

    def __str__(self):
        return f"Room {self.room_number} (Floor {self.floor})"

    @property
    def current_session(self):
        """
        Returns the currently active WiFi session for this room,
        or None if there is no active session.
        """
        return self.wifi_sessions.filter(is_active=True).order_by('-created_at').first()


class SystemSettings(models.Model):
    """
    Global settings for the WiFi system.
    Enforced as a Singleton (only one instance can exist).
    """
    wifi_ssid = models.CharField(
        max_length=50,
        default="Hotel_Guest_WiFi",
        help_text="The name of the WiFi network displayed on the PDF ticket."
    )
    password_preset_chars = models.CharField(
        max_length=100,
        default="ABCDEFGHJKLMNPQRSTUVWXYZ23456789",
        help_text="Characters used to generate passwords. Avoid easily confused chars like 0, O, 1, l, I."
    )
    default_password_length = models.IntegerField(
        default=8,
        help_text="Default length for auto-generated passwords."
    )

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        # Singleton logic: Ensure only one instance of SystemSettings exists
        self.pk = 1
        super(SystemSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        # Helper method to easily fetch the settings anywhere in the app
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Global WiFi System Settings"