# 🐾 Care-Tracker

A household pet care tracking system that helps multiple family members coordinate care tasks for pets. Track medications, feedings, supplements, and more with a complete history log.

## Features

- **Multi-user access**: No authentication required - anyone on your local network can access it
- **Task tracking**: Mark care items complete with a single click
- **Undo with confirmation**: Accidentally marked something? Undo it (with confirmation to prevent mistakes)
- **4 AM day reset**: The "care day" resets at 4 AM, not midnight, so late-night care counts for the current day
- **Full history**: All actions logged with timestamps
- **Mobile-friendly**: Responsive design works on phones and tablets
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

# Open in browser: http://localhost:8080
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
│       ├── templates/    # HTML templates
│       └── static/       # CSS and JavaScript
├── data/                 # SQLite database
├── requirements.txt      # Python dependencies
├── run.py               # Convenience run script
└── architecture.md      # Detailed architecture docs
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard (web UI) |
| `/history` | GET | History page (web UI) |
| `/api/pets` | GET | List all pets |
| `/api/care-items` | GET | List care items |
| `/api/status` | GET | Today's task status |
| `/api/tasks/{id}/complete` | POST | Mark task complete |
| `/api/tasks/{id}/undo` | POST | Undo task completion |
| `/api/history` | GET | Get history log |
| `/api/info` | GET | System info |

## Future Plans

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
