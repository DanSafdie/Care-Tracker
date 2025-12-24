"""
Pet Care Tracker - Main FastAPI Application

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

from database import get_db, init_db
from models import Pet, CareItem, TaskLog
from schemas import (
    PetResponse, PetCreate,
    CareItemResponse, CareItemCreate,
    TaskLogResponse, TaskStatus, DailyStatus,
    HistoryEntry
)
import crud
from utils import get_care_day, to_local_time
from seed_data import run_seed

# Create FastAPI app
app = FastAPI(
    title="Pet Care Tracker",
    description="Track pet care tasks for the whole household",
    version="1.0.0"
)

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


# ============== Startup Events ==============

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed data on startup."""
    init_db()
    # Run seed to ensure Chessie exists
    run_seed()


@app.get("/debug")
async def debug(db: Session = Depends(get_db)):
    try:
        pets = crud.get_pets(db)
        return {
            "status": "ok",
            "db_connected": True,
            "pet_count": len(pets),
            "time": datetime.now().isoformat(),
            "care_day": get_care_day().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============== Web UI Routes ==============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Main dashboard showing today's tasks."""
    try:
        care_day = get_care_day()
        daily_status = crud.get_daily_summary(db, care_day)
        now = to_local_time(datetime.utcnow())
        
        print(f"DEBUG: Rendering home for care_day={care_day}")
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "care_day": care_day,
            "daily_status": daily_status,
            "now": now
        })
    except Exception as e:
        print(f"ERROR in home route: {e}")
        print(traceback.format_exc())
        raise e


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: Session = Depends(get_db)):
    """History page showing past task completions."""
    try:
        care_day = get_care_day()
        history = crud.get_history(db, limit=100)
        
        print(f"DEBUG: Rendering history for care_day={care_day}")
        
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
            "care_day": care_day,
            "history_entries": history_entries,
            "now": to_local_time(datetime.utcnow())
        })
    except Exception as e:
        print(f"ERROR in history_page route: {e}")
        print(traceback.format_exc())
        raise e


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
        port=8000,
        reload=True
    )
