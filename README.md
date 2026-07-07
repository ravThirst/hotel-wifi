# 🏨 Hotel WiFi Management System

A web application designed for hotel staff to manage guest WiFi access. By integrating directly with **Mikrotik RouterOS Hotspots**, the system allows staff to generate, print, and manage unique WiFi passwords for individual rooms with precise checkout times.

*   **Backend:** Python, Django
*   **Database:** PostgreSQL
*   **Network Integration:** Mikrotik RouterOS API (`librouteros`)
*   **Frontend:** Django Templates, Bootstrap 5
*   **PDF Engine:** `xhtml2pdf` (with Base64 image embedding)
*   **Production Server:** Waitress (WSGI), WhiteNoise (Static Files)

---

## 🏗 Architecture & Data Models

*   **`rooms.Room`**: Represents physical hotel rooms.
*   **`rooms.SystemSettings`**: A Singleton model storing global configs (WiFi SSID, allowed password characters, default length).
*   **`wifi.WiFiSession`**: Tracks active and historical passwords, Mikrotik internal IDs, exact checkout datetimes, and the staff member who generated it.
*   **`mikrotik_api`**: A custom wrapper around `librouteros` that handles connection pooling, type-casting quirks, and raw API commands for adding users, dropping sessions, and clearing cookies.

---

## 🚀 Local Development Setup

### 1. Prerequisites
*   Python 3.10+
*   PostgreSQL
*   Access to a Mikrotik Router with Hotspot configured

### 2. Installation
```bash
git clone <your-repo-url>
cd hotel-wifi-management
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

CREATE DATABASE hotel_wifi_db;
CREATE USER wifi_user WITH PASSWORD 'YourSuperSecretDBPassword';
ALTER ROLE wifi_user SET client_encoding TO 'utf8';
ALTER ROLE wifi_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE wifi_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hotel_wifi_db TO wifi_user;

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
