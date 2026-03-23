# 🐾 Care-Tracker

## Project Overview

A household pet care tracking system that helps multiple family members coordinate care tasks for pets. Track medications, feedings, supplements, and more with a complete history log.

### Development & Deployment
- **Development**: Typically developed on macOS (MacBook Pro).
- **Production/Runtime**: Runs on **Windows** via **Docker** (specifically, a Docker Compose setup).
- **Cross-Platform**: The system is built to be fully compatible with both environments.

### Identifying the Production Environment & Applying Changes
If you are an AI agent working in this repository and the workspace path is `C:\Users\danie\Documents\Docker\Care-Tracker` (or similar Windows path with Docker in the name), **you are in the production environment**.

**CRITICAL RULES FOR PRODUCTION:**
1. **Docker Compose Overrides:** The `docker-compose.override.yml` file mounts the local `./app` directory into the container. This means changes to Python files (`.py`), HTML templates (`.html`), and static assets (`.js`, `.css`) will take effect *immediately* without a container restart (thanks to FastAPI's `--reload` flag and live volume mounts).
2. **Applying Changes:** 
   - For code/frontend changes: Just save the files. The live volume mount handles it.
   - For `requirements.txt` / dependency changes: You MUST rebuild the container using `docker compose up -d --build`.
   - For `Dockerfile` or `docker-compose.yml` changes: You MUST rebuild/restart the container using `docker compose up -d --build`.
3. **No Downtime:** Avoid running `docker compose down` unless absolutely necessary, as it causes downtime. Use `docker compose up -d --build` to seamlessly recreate the container.

## Features

- **"Soft" User Identity**: No passwords required for household use. Users "check-in" with a name that persists via `localStorage` and resolves to a central `users` registry in the database.
- **Eventual Auth Ready**: The system is architected to transition to full authentication (FastAPI-Users, JWT) if public exposure or private profiles (e.g., for SMS reminders) are needed.
- **Task tracking**: Mark care items complete with a single click
- **Undo with confirmation**: Accidentally marked something? Undo it (with confirmation to prevent mistakes)
- **4 AM day reset**: The "care day" resets at 4 AM, not midnight, so late-night care counts for the current day
- **Full history**: All actions logged with timestamps
- **Intelligent Timers**: Coordinating medications like Denamarin with meal times (logic: 2hr wait after food if medication pending, 1hr wait after medication if meal pending)
- **Mobile-friendly**: Responsive design works on phones and tablets
- **Kiosk mode**: Dedicated dark-mode, touch-first dashboard (`/kiosk`) for always-on tablets (designed for Amazon Fire HD 10 w/ Fully Kiosk Browser)
- **Extensible**: Easy to add new pets, care items, or responsibilities

## Current Configuration

**Pet**: Chessie (dog)

**Care Items**:
| Item | Category | Notes |
|------|----------|-------|
| Denamarin | Medication | Give on empty stomach, at least 1 hour before food |
| Ursodiol | Medication | Give with food |
| Fish Oil | Supplement | Give with food |
| Breakfast | Food | - |
| Dinner | Food | - |
| Cosequin | Supplement | Give with food |

## Quick Start

### Prerequisites
- Python 3.12+

### Run Locally

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py

# Open in browser: http://localhost:8273
```

### Running Tests

To run the automated test suite (checks API, core logic, and page loading):

```bash
# Run all tests
python run.py --test
```

### Access from Other Devices

The server binds to `0.0.0.0` by default, making it accessible from other devices on your network. Find your machine's IP address and access `http://YOUR_IP:8080`.

## Project Structure

```
├── app/
│   ├── backend/          # FastAPI application
│   │   ├── main.py       # Routes and app setup
│   │   ├── models.py     # Database models
│   │   ├── crud.py       # Database operations
│   │   └── ...
│   └── frontend/         # Web UI
│       ├── templates/    # HTML templates (index, kiosk, history, etc.)
│       └── static/       # CSS and JavaScript (main + kiosk variants)
├── data/                 # SQLite database
├── tests/                # Pytest test suite
├── requirements.txt      # Python dependencies
├── run.py               # Convenience run script
└── architecture.md      # Detailed architecture docs
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard (web UI) |
| `/kiosk` | GET | Kiosk dashboard — dark, touch-first, always-on tablet UI |
| `/history` | GET | History page (web UI) |
| `/api/pets` | GET | List all pets |
| `/api/care-items` | GET | List care items |
| `/api/status` | GET | Today's task status |
| `/api/tasks/{id}/complete` | POST | Mark task complete |
| `/api/tasks/{id}/undo` | POST | Undo task completion |
| `/api/users/search` | GET | Search for existing caretakers |
| `/api/users/check-in` | POST | Register or update user presence |
| `/api/history` | GET | Get history log |
| `/api/info` | GET | System info |

## Future Plans

- **Full Authentication**: Optional transition to a library-based auth system (e.g. FastAPI-Users) for private profiles and sensitive data (phone numbers, email).
- **Docker & Remote Access**: Containerized deployment with Tailscale/Cloudflare for multi-house synchronization.
- **Physical Button Integration**: Support for Zigbee/Z-Wave buttons (IKEA SOMRIG, Aqara) for "one-click" logging.
- **Ambient LED Warnings**: State-based lighting in the kitchen (Green/Yellow/Red) to signal care status without checking a phone.
- **Portable Care Kit**: A smart medication box that travels between houses and maintains a connection to the central server.
- **Rule Enforcement**: Validate timing/dependencies between care items (e.g., empty stomach rules).
- **Notifications**: Automated reminders when tasks are overdue or delinquent.
- **Multi-Pet Expansion**: Full support for varying schedules across multiple animals.

## Screenshots

Access the dashboard at `http://localhost:8000`:
- View all care tasks for today
- Green cards = completed, gray = pending
- Click "Mark Complete" or "Undo" to update status

View history at `http://localhost:8000/history`:
- See all past completions and undos
- Filter by date, pet, or task

## License

MIT
