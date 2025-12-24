# Care-Tracker - Architecture

## Overview

A household pet care tracking system that enables multiple family members to coordinate care tasks for pets. The system tracks medications, feedings, supplements, and other care items with a complete history log.

## Key Features

- **Multi-user access**: No authentication required for household use on local network
- **Task tracking**: Mark care items complete, with undo capability (with confirmation)
- **4 AM day reset**: The "care day" resets at 4 AM, not midnight, to handle late-night care
- **Timer functionality**: Smart timers for medication/feeding intervals (e.g., 2hr wait after food for Denamarin)
- **Full history**: All actions logged with timestamps and optional user identification
- **Extensible design**: Built to accommodate future rule sets, additional pets, and integrations

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Python + FastAPI | Fast async API, easy to extend, great docs |
| Database | SQLite + SQLAlchemy | Simple file-based DB, no server needed, perfect for local use |
| Frontend | Jinja2 templates + Vanilla JS | Lightweight, no build step, works everywhere |
| Server | Uvicorn | Production-ready ASGI server |

## Project Structure

```
/workspace/
├── app/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application & routes
│   │   ├── database.py      # DB connection & session management
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── crud.py          # Database operations
│   │   ├── utils.py         # Utilities (care day calculation, etc.)
│   │   └── seed_data.py     # Initial data seeding
│   │
│   └── frontend/
│       ├── templates/
│       │   ├── base.html    # Base template with nav/footer
│       │   ├── index.html   # Dashboard (today's tasks)
│       │   └── history.html # History log view
│       │
│       └── static/
│           ├── css/
│           │   └── style.css
│           └── js/
│               └── app.js
│
├── data/                     # SQLite database storage
├── requirements.txt          # Python dependencies
├── run.py                    # Convenience run script
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose for local/server deployment
└── architecture.md           # This file
```

## Data Models

### Pet
Represents a pet in the household.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| name | string | Pet's name (e.g., "Chessie") |
| species | string | Type of pet (e.g., "dog") |
| notes | text | General notes about the pet |
| is_active | bool | Soft delete flag |
| created_at | datetime | Record creation time |

### CareItem
A care task associated with a pet.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| pet_id | int | Foreign key to Pet |
| name | string | Task name (e.g., "Denamarin") |
| description | text | What this item is |
| notes | text | Timing/dependency info (informational only) |
| category | string | medication, food, supplement, etc. |
| display_order | int | UI ordering |
| is_active | bool | Soft delete flag |

### TaskLog
Historical record of task completions and undos.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Primary key |
| care_item_id | int | Foreign key to CareItem |
| care_day | date | Logical care day (resets at 4 AM) |
| action | string | 'completed' or 'undone' |
| completed_by | string | Optional: who did it |
| timestamp | datetime | When the action occurred |
| notes | text | Optional notes |

## API Endpoints

### Pets
- `GET /api/pets` - List all active pets
- `POST /api/pets` - Create a new pet
- `GET /api/pets/{id}` - Get specific pet

### Care Items
- `GET /api/care-items` - List care items (optional `?pet_id=` filter)
- `POST /api/care-items` - Create a care item

### Tasks
- `GET /api/status` - Get today's status for all pets/tasks
- `POST /api/tasks/{id}/complete` - Mark task complete
- `POST /api/tasks/{id}/undo` - Undo task completion

### History
- `GET /api/history` - Get task history with optional filters

### System
- `GET /api/info` - Get system info (care day, version, etc.)

## Timer Functionality

The system includes a smart timer feature to help manage dependencies between tasks, particularly coordinating Denamarin (liver supplement) with meal timing.

### Features
- **Intelligent meal-based triggers**: The system intelligently prompts for timers based on task dependencies:
  - **Breakfast/Dinner → Denamarin**: When either meal is completed and Denamarin is still pending, offers a 2-hour "Empty stomach" timer
  - **Denamarin → Next Meal**: When Denamarin is completed and meals are still pending, offers a 1-hour "Next meal ready" timer
  - **Smart skipping**: If Denamarin is completed after both meals are done, NO timer is offered (no meals remaining today)
- **Multi-device coordination**: Timer state is stored **server-side** in the database, allowing any household member to see the same timer status regardless of which device they use
- **Visual indicators**: A compact, gradient-styled timer badge appears in the top right of the pet's header when active
- **Ready state**: When the timer reaches zero, it displays "READY!" with visual emphasis
- **Automatic replacement**: Setting a new timer automatically clears any existing timer for that pet
- **Mobile responsive**: Timer wraps gracefully on mobile devices without breaking layout

### Timer Logic (Centralized)
All timer prompting logic is housed in one function: `handleTimerPrompts()` in `app/frontend/static/js/app.js`

**Decision tree:**
```
Meal completed (Breakfast/Dinner):
  - If Denamarin NOT completed → Offer 2hr timer ("Empty stomach")
  - If Denamarin already completed → No timer

Denamarin completed:
  - If ANY meal still pending → Offer 1hr timer ("Next meal ready")
  - If ALL meals already completed → No timer (no more meals today)
```

### Implementation
- **Backend**: `Pet` model includes `timer_end_time` and `timer_label` fields
- **API Endpoints**: 
  - `POST /api/pets/{id}/timer?hours={hours}&label={label}` - Set a timer
  - `DELETE /api/pets/{id}/timer` - Clear a timer
- **Frontend**: JavaScript countdown updates every second, with server data as source of truth on page load
- **Timezone handling**: Uses local time (not UTC) for consistency with household timezone

## 4 AM Day Reset Logic

The "care day" does not follow calendar days. Instead:
- 4:00 AM is the start of a new care day
- 3:59 AM still belongs to the previous care day

This handles the common scenario where late-night care (before bed) should still count as "today's" tasks.

Example:
- At 11:30 PM on Jan 1st → care day is Jan 1st
- At 2:00 AM on Jan 2nd → care day is still Jan 1st
- At 4:00 AM on Jan 2nd → care day becomes Jan 2nd

## Future Extensions

### Rule Sets (Planned)
The `notes` field on CareItem currently contains human-readable timing info (e.g., "Give on empty stomach"). Future versions could parse this into enforceable rules:
- Time-based rules (morning only, with dinner, etc.)
- Dependency rules (must give X before Y)
- Interval rules (every 8 hours)

### Home Assistant Integration (Planned)
The API design supports future integration with Home Assistant for:
- LED status indicators (green = all done, red = pending)
- Notifications when tasks are overdue
- Voice control via Alexa/Google Home

### Multi-Pet Expansion
The data model already supports multiple pets. Adding a new pet:
1. Create pet via API
2. Add care items for that pet
3. Dashboard automatically shows all active pets

## Running the Application

### Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py

# Access at http://localhost:8080
```

### Docker (Planned)

The application is designed to be containerized for robust deployment across multiple locations:
- **Persistence**: SQLite database stored in `/data` volume to persist history across container updates.
- **Remote Access**: Recommended deployment behind **Tailscale** or a **Cloudflare Tunnel** for secure, multi-house access without port forwarding.
- **Single Source of Truth**: Hosting the container at a primary residence (House 1) allows secondary locations (House 2, mobile) to sync with the same database.

## Distributed Household Architecture (Planned)

To support a "traveling care kit" (e.g., meds moving between houses), the following architecture is proposed:

### 1. Centralized Brain
- A single Docker instance running at "House 1" acts as the global coordinator.
- All devices (phones, physical buttons, LED strips) in all houses connect to this central instance via a private mesh network (Tailscale).

### 2. Location Awareness
- Future `TaskLog` entries will include a `location` field (e.g., "House 1", "House 2", "Mobile") to track where care was provided.
- Allows for different rule sets or reminders based on the current physical location of the pet.

### 3. Portable Care Kit
- An ESP32-powered "Smart Care Box" that travels with the pet.
- Features physical buttons for logging and an LED status indicator that pulses based on the central server's state.

## Hardware Integration (Planned)

The system is designed to bridge the digital and physical worlds for lower friction in the kitchen:

### 1. Physical Buttons (Zigbee/Z-Wave)
- **Buttons-on-Caps**: Small Zigbee buttons (e.g., Aqara Mini Switch) mounted directly on medication bottle caps for "Tap-to-Log" functionality.
- **Stationary Hubs**: Multi-button remotes (e.g., IKEA SOMRIG) mounted in the kitchen or on the care box to log feedings and supplements.

### 2. Ambient State Indicators
- **LED Status Bar**: Addressable LED strips (NeoPixels) that change color based on the pet's current care status:
  - **Green**: All tasks for the current block are complete.
  - **Yellow Pulse**: A task is approaching delinquency (e.g., past "ideal time").
  - **Red**: A task is delinquent and requires immediate attention.

### 3. NFC/QR Fallback
- NFC stickers on bottles for phone-based logging.
- QR codes inside the care box lid for guests or sitters to quickly access the web UI without setup.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | Server bind address |
| PORT | 8080 | Server port |
| DATA_DIR | /workspace/data | SQLite database location |
| TZ | America/New_York | Timezone for 4 AM reset |
