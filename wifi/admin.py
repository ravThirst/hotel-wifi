from django.contrib import admin
from .models import WiFiSession


@admin.register(WiFiSession)
class WiFiSessionAdmin(admin.ModelAdmin):
    list_display = (
        'room', 
        'password', 
        'created_by', 
        'created_at', 
        'expires_at', 
        'is_active', 
        'session_status'
    )
    list_filter = ('is_active', 'created_at', 'room__floor')
    search_fields = ('room__room_number', 'password')
    readonly_fields = ('mikrotik_user_id', 'created_at')
    ordering = ('-created_at',)

    @admin.display(description='Status')
    def session_status(self, obj):
        if not obj.is_active:
            return '⚫ Deactivated'
        if obj.is_expired:
            return '🟡 Expired'
        return f'🟢 {obj.remaining_time}'

    def get_readonly_fields(self, request, obj=None):
        # Once a session is created, the password and room cannot be changed
        if obj:
            return self.readonly_fields + ('password', 'room', 'expires_at', 'created_by')
        return self.readonly_fields