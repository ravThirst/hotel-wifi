from django.contrib import admin
from .models import Room, SystemSettings


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'floor', 'is_active', 'current_password', 'session_status', 'updated_at')
    list_filter = ('floor', 'is_active')
    search_fields = ('room_number',)
    list_editable = ('is_active',)
    ordering = ('floor', 'room_number')

    @admin.display(description='Current Password')
    def current_password(self, obj):
        session = obj.current_session
        if session and session.is_active and not session.is_expired:
            return session.password
        return '—'

    @admin.display(description='Status')
    def session_status(self, obj):
        session = obj.current_session
        if not session or not session.is_active:
            return '🔴 No Active Session'
        if session.is_expired:
            return '🟡 Expired (Pending Reset)'
        return f'🟢 {session.remaining_time}'


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('wifi_ssid', 'password_preset_chars', 'default_password_length')

    def has_add_permission(self, request):
        # Prevent creating a second SystemSettings instance
        if SystemSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the singleton settings
        return False