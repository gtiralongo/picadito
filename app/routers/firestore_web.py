import uuid
from datetime import datetime
from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import SITE_URL
from app.firestore_repo import FirestoreRepo

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
tpl = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def make_token():
    return uuid.uuid4().hex + uuid.uuid4().hex

def event_to_dict(event):
    # event is dict from Firestore
    participants = FirestoreRepo.list_participants(event.get('id'))
    confirmed = [p for p in participants if p.get('status') != 'cancelled']
    per_person = 0
    total = event.get('total') or 0
    max_p = event.get('max_participants') or 0
    if total > 0:
        denom = max_p if max_p > 0 else len(confirmed)
        if denom > 0:
            per_person = -(-total // denom)
    return {
        "id": event.get('id'),
        "title": event.get('title'),
        "description": event.get('description',''),
        "date": event.get('date'),
        "location": event.get('location',''),
        "address": event.get('address',''),
        "total": total,
        "deposit": event.get('deposit') or 0,
        "per_person": per_person,
        "max_participants": max_p,
        "creator_name": event.get('creator_name',''),
        "created_at": event.get('created_at'),
        "status": event.get('status','active'),
        "confirmed_count": len(confirmed),
        "total_guests": sum(p.get('guests',1) for p in confirmed),
        "participants": confirmed,
    }

@router.get("/")
def index(request: Request):
    return tpl.TemplateResponse("index.html", {"request": request})

@router.get("/crear")
def create_form(request: Request):
    return tpl.TemplateResponse("create.html", {"request": request})

@router.post("/crear")
def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    date: str = Form(...),
    location: str = Form(""),
    address: str = Form(""),
    total: int = Form(0),
    deposit: int = Form(0),
    max_participants: int = Form(0),
    creator_name: str = Form(...),
):
    try:
        event_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "Fecha inválida")
    event_data = {
        "title": title,
        "description": description,
        "date": event_date,
        "location": location,
        "address": address,
        "total": max(total,0),
        "deposit": max(deposit,0),
        "max_participants": max_participants,
        "creator_name": creator_name,
        "creator_token": make_token(),
        "status": "active",
    }
    ev = FirestoreRepo.create_event(event_data)
    return RedirectResponse(url=f"/e/{ev['id']}", status_code=303)

@router.get("/e/{event_id}")
def event_detail(request: Request, event_id: str):
    event = FirestoreRepo.get_event(event_id)
    if not event:
        raise HTTPException(404, "Evento no encontrado")
    if event.get('status') == 'cancelled':
        return tpl.TemplateResponse("event_cancelled.html", {"request": request, "event": event})
    event_dict = event_to_dict(event)
    return tpl.TemplateResponse("event.html", {
        "request": request,
        "event": event,
        "event_dict": event_dict,
        "site_url": SITE_URL,
    })

@router.post("/e/{event_id}/participar")
def participate(
    request: Request,
    event_id: str,
    name: str = Form(...),
    phone: str = Form(""),
    guests: int = Form(1),
):
    event = FirestoreRepo.get_event(event_id)
    if not event or event.get('status') == 'cancelled':
        raise HTTPException(404, "Evento no encontrado")
    max_p = event.get('max_participants') or 0
    participants = FirestoreRepo.list_participants(event_id)
    confirmed = [p for p in participants if p.get('status') != 'cancelled']
    current = sum(p.get('guests',1) for p in confirmed)
    if max_p > 0 and current + guests > max_p:
        return JSONResponse(status_code=400, content={"error": "No quedan cupos disponibles"})
    participant_data = {
        "name": name,
        "phone": phone,
        "guests": guests,
        "token": make_token(),
        "status": "confirmed",
        "team": None,
    }
    p = FirestoreRepo.create_participant(event_id, participant_data)
    return JSONResponse(content={
        "ok": True,
        "participant_token": p['token'],
        "edit_url": f"{SITE_URL}/p/{p['token']}",
    })
