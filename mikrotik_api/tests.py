from mikrotik_api.hotspot import add_hotspot_user, drop_active_session, remove_hotspot_user
add_hotspot_user(room_number="999", password="TestPass123", uptime_limit="1h")
remove_hotspot_user("999")
drop_active_session("admin")

# import os
# from mikrotik_api.hotspot import add_hotspot_user
# from mikrotik_api.exceptions import MikrotikConnectionError
#
# try:
#     print("Attempting to add user to offline router...")
#     add_hotspot_user("101", "Password123", "24h")
# except MikrotikConnectionError as e:
#     print(f"Caught Custom Exception successfully! Message: {e}")
# except Exception as e:
#     print(f"Failed to catch properly. Raw error: {type(e)}")
#
# # 2. Restore the IP for future steps
# from dotenv import load_dotenv
# load_dotenv(override=True)
#
# exit()
