"""
Care-Tracker - Main FastAPI Application

A household pet care tracking system that allows multiple family members
to track and coordinate pet care tasks like medications, feeding, and supplements.

Features:
- Track multiple pets and their care items
- Mark tasks complete/undo with history logging
- Day resets at 4 AM (configurable)
- Full history/audit log
- Extensible for future rule sets and integrations (e.g., Home Assistant LEDs)
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List, Optional
import os
import traceback
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from database import get_db, init_db, SessionLocal
from models import Pet, CareItem, TaskLog, User
from schemas import (
    PetResponse, PetCreate,
    CareItemResponse, CareItemCreate,
    TaskLogResponse, TaskStatus, DailyStatus,
    HistoryEntry, UserResponse, UserCreate, UserUpdate,
    CheckInResponse
)
import crud
from utils import get_care_day, to_local_time
from seed_data import run_seed
from sms_utils import send_sms
from hass_utils import call_hass_script

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Care-Tracker",
    description="Track pet care tasks for the whole household",
    version="1.0.0"
)

# ============== Helper Functions ==============

def send_user_alert_confirmation(user: User):
    """
    Sends a confirmation SMS when a user enables or updates their alert settings.
    """
    if not user.wants_alerts or not user.phone_number:
        return
    
    expiry_text = f" until {user.alert_expiry_date}" if user.alert_expiry_date else ""
    message = f"🐶 Care-Tracker: Welcome to the pack, {user.name}! Your phone is now linked for pet care alerts. We'll keep you posted{expiry_text}!"
    
    logger.info(f"Sending alert confirmation to {user.name} ({user.phone_number})")
    send_sms(user.phone_number, message)

# Exception handling middleware for debugging
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        print(f"!!! EXCEPTION CAUGHT BY MIDDLEWARE !!!")
        print(traceback.format_exc())
        # If it's an API request, return JSON
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc), "traceback": traceback.format_exc()}
            )
        # Otherwise, we'll let it raise so we can see it in the console/logs
        # but for a production-like feel we could return a 500 HTML page
        raise exc

# Mount static files (CSS, JS)
static_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
templates_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates")

app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# Add custom Jinja2 filter for timezone conversion
def jinja_strftime(dt, fmt):
    if not dt:
        return ""
    return dt.strftime(fmt)

templates.env.filters["local_time"] = to_local_time
templates.env.filters["strftime"] = jinja_strftime


def sync_led_status(db: Session):
    """
    Synchronize the Inovelli LED state with current timer statuses.
    Priority: Expired (Green Pulse) > Running (Yellow Solid) > None (Clear)
    """
    try:
        expired_count = crud.get_expired_timers_count(db)
        if expired_count > 0:
            call_hass_script("downstairs_spotlight_led_green_pulse")
            return

        active_count = crud.get_active_timers_count(db)
        if active_count > 0:
            call_hass_script("downstairs_spotlight_led_yellow_solid")
            return

        # No timers active or expired
        call_hass_script("downstairs_spotlight_led_clear")
    except Exception as e:
        logger.error(f"Error syncing LED status: {e}")


# ============== Startup Events ==============

# ============== Scheduler Setup ==============

scheduler = BackgroundScheduler()

def check_timers_job():
    """Poll for expired timers and send SMS alerts."""
    db = SessionLocal()
    try:
        now = datetime.now()
        # Find pets with expired timers that haven't been alerted yet
        expired_pets = db.query(Pet).filter(
            Pet.timer_end_time != None,
            Pet.timer_end_time <= now,
            Pet.timer_alert_sent == False
        ).all()
        
        if not expired_pets:
            return
            
        # Get users who should receive alerts
        users = db.query(User).filter(
            User.wants_alerts == True,
            User.phone_number != None,
            (User.alert_expiry_date == None) | (User.alert_expiry_date >= get_care_day())
        ).all()
        
        if not users:
            # Still mark as alerted so they don't keep trying every minute
            for pet in expired_pets:
                pet.timer_alert_sent = True
            db.commit()
            return

        for pet in expired_pets:
            message = f"⏰ Timer for {pet.name} ({pet.timer_label}) has run out!"
            for user in users:
                send_sms(user.phone_number, message)
            
            # Mark the timer as alerted so it doesn't alert again
            # BUT keep the timer fields so it stays "READY!" in the UI
            pet.timer_alert_sent = True
        
        db.commit()
        
        # Sync LED status after checking timers
        sync_led_status(db)
    except Exception as e:
        print(f"Error in check_timers_job: {e}")
        db.rollback()
    finally:
        db.close()


def nightly_reminder_job():
    """Send a summary of incomplete tasks at 9 PM."""
    db = SessionLocal()
    try:
        # Get users who should receive alerts
        users = db.query(User).filter(
            User.wants_alerts == True,
            User.phone_number != None,
            (User.alert_expiry_date == None) | (User.alert_expiry_date >= get_care_day())
        ).all()
        
        if not users:
            return

        # Get daily summary
        care_day = get_care_day()
        summary = crud.get_daily_summary(db, care_day)
        
        incomplete_tasks = []
        for pet_data in summary:
            pet_name = pet_data['pet'].name
            pending = [t['care_item'].name for t in pet_data['tasks'] if not t['is_completed']]
            if pending:
                incomplete_tasks.append(f"{pet_name}: {', '.join(pending)}")
        
        if not incomplete_tasks:
            # Everything done! (Maybe send a "Good job" text? Plan doesn't specify, so let's skip for now to save Twilio credits)
            return

        message = "🌙 Nightly Reminder - Still to do:\n" + "\n".join(incomplete_tasks)
        for user in users:
            send_sms(user.phone_number, message)
            
    except Exception as e:
        print(f"Error in nightly_reminder_job: {e}")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize database and seed data on startup."""
    init_db()
    # Run seed to ensure Chessie exists
    run_seed()
    
    # Start scheduler
    if not scheduler.running:
        scheduler.add_job(check_timers_job, 'interval', minutes=1, id='check_timers')
        # Nightly reminder at 9 PM (21:00)
        scheduler.add_job(nightly_reminder_job, 'cron', hour=21, minute=0, id='nightly_reminder')
        scheduler.start()
        print("Background scheduler started.")
        
        # Initial LED sync
        db = SessionLocal()
        try:
            sync_led_status(db)
        finally:
            db.close()


# ============== Web UI Routes ==============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard showing today's tasks."""
    care_day = get_care_day()
    daily_status = crud.get_daily_summary(db, care_day)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "care_day": care_day,
        "daily_status": daily_status,
        "now": to_local_time(datetime.utcnow())
    })


@app.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request, 
    view: str = "grid", 
    page: int = 1, 
    db: Session = Depends(get_db)
):
    """History page showing past task completions."""
    care_day = get_care_day()
    
    if view == "grid":
        grid_data = crud.get_grid_history(db, page=page, page_size=30)
        return templates.TemplateResponse("history.html", {
            "request": request,
            "view": view,
            "grid_data": grid_data,
            "care_day": care_day,
            "now": to_local_time(datetime.utcnow())
        })
    else:
        # List view (existing logic)
        history = crud.get_history(db, limit=100)
        
        # Enrich with pet/item names
        history_entries = []
        for log in history:
            care_item = crud.get_care_item(db, log.care_item_id)
            pet = crud.get_pet(db, care_item.pet_id) if care_item else None
            history_entries.append({
                "log": log,
                "pet_name": pet.name if pet else "Unknown",
                "care_item_name": care_item.name if care_item else "Unknown"
            })
        
        return templates.TemplateResponse("history.html", {
            "request": request,
            "view": view,
            "care_day": care_day,
            "history_entries": history_entries,
            "now": to_local_time(datetime.utcnow())
        })


@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request):
    """Render the account management page."""
    care_day = get_care_day()
    return templates.TemplateResponse("account.html", {
        "request": request,
        "care_day": care_day,
        "now": to_local_time(datetime.utcnow())
    })


@app.get("/api/history/grid")
async def get_grid_history_api(page: int = 1, page_size: int = 30, db: Session = Depends(get_db)):
    """API endpoint for grid history data."""
    return crud.get_grid_history(db, page=page, page_size=page_size)


# ============== API Routes - Pets ==============

@app.get("/api/pets", response_model=List[PetResponse])
async def get_pets(db: Session = Depends(get_db)):
    """Get all active pets."""
    return crud.get_pets(db)


@app.post("/api/pets", response_model=PetResponse)
async def create_pet(pet: PetCreate, db: Session = Depends(get_db)):
    """Create a new pet."""
    return crud.create_pet(db, pet)


@app.get("/api/pets/{pet_id}", response_model=PetResponse)
async def get_pet(pet_id: int, db: Session = Depends(get_db)):
    """Get a specific pet by ID."""
    pet = crud.get_pet(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@app.post("/api/pets/{pet_id}/timer")
async def set_pet_timer(
    pet_id: int,
    hours: float,
    label: str,
    db: Session = Depends(get_db)
):
    """Set a timer for a pet."""
    pet = crud.set_pet_timer(db, pet_id, hours, label)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    sync_led_status(db)
    return {"success": True, "pet": pet}


@app.delete("/api/pets/{pet_id}/timer")
async def clear_pet_timer(pet_id: int, db: Session = Depends(get_db)):
    """Clear a timer for a pet."""
    pet = crud.clear_pet_timer(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    sync_led_status(db)
    return {"success": True, "pet": pet}


# ============== API Routes - Users ==============

@app.get("/api/users/search", response_model=List[UserResponse])
async def search_users(q: str = "", db: Session = Depends(get_db)):
    """Search for existing usernames."""
    return crud.search_users(db, q)


@app.post("/api/users/check-in", response_model=CheckInResponse)
async def check_in_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register or update a user's presence."""
    db_user, is_new = crud.get_or_create_user(
        db, 
        user.name, 
        phone_number=user.phone_number,
        wants_alerts=user.wants_alerts,
        alert_expiry_date=user.alert_expiry_date
    )
    
    # Trigger SMS if this is a registration with alert info provided
    if is_new and db_user.wants_alerts and db_user.phone_number:
        send_user_alert_confirmation(db_user)
        
    return {"user": db_user, "is_new": is_new}


@app.get("/api/users/by-name/{name}", response_model=UserResponse)
async def get_user_by_name(name: str, db: Session = Depends(get_db)):
    """Get a user by their name."""
    user = crud.get_user_by_name(db, name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user's profile and notification settings."""
    user = crud.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Trigger SMS whenever alert settings are "saved" (updated)
    # The user specifically requested this to re-trigger on any save of alert info
    if user.wants_alerts and user.phone_number:
        send_user_alert_confirmation(user)
        
    return user


# ============== API Routes - Care Items ==============

@app.get("/api/care-items", response_model=List[CareItemResponse])
async def get_care_items(pet_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get care items, optionally filtered by pet."""
    return crud.get_care_items(db, pet_id=pet_id)


@app.post("/api/care-items", response_model=CareItemResponse)
async def create_care_item(care_item: CareItemCreate, db: Session = Depends(get_db)):
    """Create a new care item for a pet."""
    # Verify pet exists
    pet = crud.get_pet(db, care_item.pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return crud.create_care_item(db, care_item)


# ============== API Routes - Task Status ==============

@app.get("/api/status")
async def get_daily_status(db: Session = Depends(get_db)):
    """
    Get the current day's status for all pets and tasks.
    This is the main endpoint for the dashboard.
    """
    care_day = get_care_day()
    return {
        "care_day": care_day.isoformat(),
        "pets": crud.get_daily_summary(db, care_day)
    }


@app.post("/api/tasks/{care_item_id}/complete")
async def complete_task(
    care_item_id: int,
    completed_by: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Mark a task as completed for today.
    """
    # Verify care item exists
    care_item = crud.get_care_item(db, care_item_id)
    if not care_item:
        raise HTTPException(status_code=404, detail="Care item not found")
    
    # Check if already completed
    care_day = get_care_day()
    if crud.get_task_status_for_day(db, care_item_id, care_day):
        raise HTTPException(status_code=400, detail="Task already completed for today")
    
    log = crud.complete_task(db, care_item_id, completed_by, notes)
    print(f"TASK COMPLETED: Item {care_item_id} ({care_item.name}) by {completed_by or 'Unknown'}")
    return {
        "success": True,
        "message": f"{care_item.name} marked as complete",
        "log_id": log.id
    }


@app.post("/api/tasks/{care_item_id}/undo")
async def undo_task(
    care_item_id: int,
    completed_by: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Undo a completed task for today.
    """
    # Verify care item exists
    care_item = crud.get_care_item(db, care_item_id)
    if not care_item:
        raise HTTPException(status_code=404, detail="Care item not found")
    
    # Check if actually completed
    care_day = get_care_day()
    if not crud.get_task_status_for_day(db, care_item_id, care_day):
        raise HTTPException(status_code=400, detail="Task is not completed")
    
    log = crud.undo_task(db, care_item_id, completed_by, notes)
    print(f"TASK UNDONE: Item {care_item_id} ({care_item.name})")
    return {
        "success": True,
        "message": f"{care_item.name} marked as not complete",
        "log_id": log.id
    }


# ============== API Routes - History ==============

@app.get("/api/history", response_model=List[TaskLogResponse])
async def get_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    pet_id: Optional[int] = None,
    care_item_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get task history with optional filters.
    """
    return crud.get_history(
        db,
        start_date=start_date,
        end_date=end_date,
        pet_id=pet_id,
        care_item_id=care_item_id,
        limit=limit
    )


@app.get("/api/info")
async def get_info():
    """Get system info including current care day."""
    care_day = get_care_day()
    return {
        "care_day": care_day.isoformat(),
        "current_time": to_local_time(datetime.utcnow()).isoformat(),
        "day_reset_hour": 4,
        "version": "1.0.0"
    }


# ============== Run with Uvicorn ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8273,
        reload=True
    )
