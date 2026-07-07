from django.db import models
from django.utils import timezone
from rooms.models import Room

class WiFiSession(models.Model):
    """
    Represents an active or expired WiFi password session for a specific room.
    A room can have many sessions over time, but only one should be active at any given moment.
    """
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='wifi_sessions',
        help_text="The hotel room this session belongs to."
    )
    password = models.CharField(
        max_length=50,
        help_text="The WiFi password generated for this session."
    )
    mikrotik_user_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The internal ID of the user entry on the Mikrotik router."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        verbose_name="Checkout Date & Time",
        help_text="The exact date and time the guest checks out and WiFi expires."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this session is currently active."
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sessions',
        help_text="The staff member who generated this session."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "WiFi Session"
        verbose_name_plural = "WiFi Sessions"
        # Ensure the router-side username is unique when active
        indexes = [
            models.Index(fields=['room', 'is_active']),
        ]

    def __str__(self):
        status = "Active" if self.is_active else "Expired"
        return f"Session for Room {self.room.room_number} ({status})"

    @property
    def is_expired(self):
        """Check if the session has passed its expiration time."""
        return timezone.now() >= self.expires_at

    @property
    def remaining_time(self):
        """Return a highly precise human-readable string of time remaining."""
        if not self.is_active or self.is_expired:
            return "Expired"

        delta = self.expires_at - timezone.now()
        total_seconds = int(delta.total_seconds())

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")

        return " ".join(parts) if parts else "Less than 1m"