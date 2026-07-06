from wifi.utils import generate_wifi_password
from rooms.models import SystemSettings

# 1. Test default generation
print("--- DEFAULT GENERATION ---")
pwd1 = generate_wifi_password()
print(f"Generated Password: {pwd1}")
print(f"Length: {len(pwd1)}")

# 2. Test custom length override
print("\n--- CUSTOM LENGTH OVERRIDE ---")
pwd2 = generate_wifi_password(length=12)
print(f"Generated Password (12 chars): {pwd2}")

# 3. Test dynamic DB updates
print("\n--- DYNAMIC DB UPDATE ---")
settings = SystemSettings.load()
print(f"Current allowed chars: {settings.password_preset_chars}")

# Let's change the settings to ONLY numbers and lowercase letters
settings.password_preset_chars = "abcdefghij1234567890"
settings.default_password_length = 6
settings.save()

# Generate a new password - it should now only contain our new characters!
pwd3 = generate_wifi_password()
print(f"New Password (only a-j and 0-9): {pwd3}")
print(f"New Length: {len(pwd3)}")

# 4. Clean up: Reset the settings back to normal for future steps
settings.password_preset_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
settings.default_password_length = 8
settings.save()
print("\nSettings reset to default.")

exit()