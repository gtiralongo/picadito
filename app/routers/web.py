import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, Participant, Notification
from app.config import SITE_URL
from app.routers.auth import get_logged_user

router = APIRouter()


def make_token():
    return uuid.uuid4().hex + uuid.uuid4().hex


def event_to_dict(event: Event):
    confirmed = [p for p in event.participants if p.status == "confirmed"]
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date,
        "location": event.location,
        "max_participants": event.max_participants,
        "creator_name": event.creator_name,
        "created_at": event.created_at,
        "status": event.status,
        "confirmed_count": len(confirmed),
        "total_guests": sum(p.guests for p in confirmed),
    }


def render_template(request: Request, name: str, **context):
    from app.main import tpl
    return tpl.TemplateResponse(name, {"request": request, **context})


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    return render_template(request, "index.html", user=get_logged_user(request, db))


@router.get("/crear")
def create_form(request: Request, db: Session = Depends(get_db)):
    return render_template(request, "create.html", user=get_logged_user(request, db))


@router.post("/crear")
def create_event(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    date: str = Form(...),
    location: str = Form(""),
    max_participants: int = Form(0),
    creator_name: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        event_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "Fecha inválida")

    user = get_logged_user(request, db)
    event = Event(
        title=title,
        description=description,
        date=event_date,
        location=location,
        max_participants=max_participants,
        creator_name=creator_name,
        creator_token=make_token(),
        creator_id=user.id if user else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return RedirectResponse(
        url=f"/admin/{event.id}/{event.creator_token}", status_code=303
    )


@router.get("/e/{event_id}")
def event_detail(request: Request, event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "Evento no encontrado")
    if event.status == "cancelled":
        return render_template(request, "event_cancelled.html", event=event, user=get_logged_user(request, db))

    series_events = []
    if event.series_id:
        series_events = (
            db.query(Event)
            .filter(Event.series_id == event.series_id)
            .order_by(Event.date)
            .all()
        )

    return render_template(
        request,
        "event.html",
        event=event,
        event_dict=event_to_dict(event),
        series_events=series_events,
        site_url=SITE_URL,
        user=get_logged_user(request, db),
    )


@router.post("/e/{event_id}/participar")
def participate(
    request: Request,
    event_id: str,
    name: str = Form(...),
    phone: str = Form(""),
    guests: int = Form(1),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.status == "cancelled":
        raise HTTPException(404, "Evento no encontrado")

    if event.max_participants > 0:
        current = sum(p.guests for p in event.participants if p.status == "confirmed")
        if current + guests > event.max_participants:
            return JSONResponse(
                status_code=400,
                content={"error": "No quedan cupos disponibles"},
            )

    participant = Participant(
        event_id=event_id,
        name=name,
        phone=phone,
        token=make_token(),
        guests=guests,
    )
    db.add(participant)

    notif = Notification(
        event_id=event_id,
        message=f"{name} se anotó{' (+' + str(guests-1) + ')' if guests > 1 else ''}",
    )
    db.add(notif)
    db.commit()
    db.refresh(participant)

    return JSONResponse(
        content={
            "ok": True,
            "participant_token": participant.token,
            "edit_url": f"{SITE_URL}/p/{participant.token}",
        }
    )


@router.get("/p/{participant_token}")
def participant_edit(
    request: Request, participant_token: str, db: Session = Depends(get_db)
):
    participant = db.query(Participant).filter(Participant.token == participant_token).first()
    if not participant:
        raise HTTPException(404, "No encontrado")

    return render_template(
        request, "participant.html",
        participant=participant,
        event=participant.event,
        user=get_logged_user(request, db),
    )


@router.post("/p/{participant_token}/cancelar")
def cancel_participation(
    request: Request,
    participant_token: str,
    db: Session = Depends(get_db),
):
    participant = db.query(Participant).filter(Participant.token == participant_token).first()
    if not participant:
        raise HTTPException(404, "No encontrado")

    participant.status = "cancelled"

    notif = Notification(
        event_id=participant.event_id,
        message=f"{participant.name} canceló",
    )
    db.add(notif)
    db.commit()

    return RedirectResponse(url=f"/p/{participant_token}", status_code=303)


@router.get("/admin/{event_id}/{creator_token}")
def admin_panel(
    request: Request,
    event_id: str,
    creator_token: str,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    unread = [n for n in event.notifications if not n.read]
    series_events = []
    if event.series_id:
        series_events = (
            db.query(Event)
            .filter(Event.series_id == event.series_id, Event.id != event.id)
            .order_by(Event.date)
            .all()
        )

    return render_template(
        request, "admin.html",
        event=event,
        event_dict=event_to_dict(event),
        site_url=SITE_URL,
        unread_count=len(unread),
        series_events=series_events,
        user=get_logged_user(request, db),
    )


@router.post("/admin/{event_id}/{creator_token}/cancelar")
def cancel_event(
    event_id: str,
    creator_token: str,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    event.status = "cancelled"
    db.commit()
    return RedirectResponse(url=f"/admin/{event_id}/{creator_token}", status_code=303)


@router.post("/admin/{event_id}/{creator_token}/editar")
def edit_event(
    request: Request,
    event_id: str,
    creator_token: str,
    title: str = Form(...),
    description: str = Form(""),
    date: str = Form(...),
    location: str = Form(""),
    max_participants: int = Form(0),
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    try:
        event_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "Fecha inválida")

    event.title = title
    event.description = description
    event.date = event_date
    event.location = location
    event.max_participants = max_participants
    db.commit()

    return RedirectResponse(url=f"/admin/{event_id}/{creator_token}", status_code=303)


@router.post("/admin/{event_id}/{creator_token}/repetir")
def repeat_event(
    event_id: str,
    creator_token: str,
    date: str = Form(...),
    db: Session = Depends(get_db),
):
    original = db.query(Event).filter(Event.id == event_id).first()
    if not original or original.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    try:
        new_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(400, "Fecha inválida")

    series_id = original.series_id or uuid.uuid4().hex

    copy = Event(
        title=original.title,
        description=original.description,
        date=new_date,
        location=original.location,
        max_participants=original.max_participants,
        creator_name=original.creator_name,
        creator_token=make_token(),
        creator_id=original.creator_id,
        series_id=series_id,
    )
    # update original with series_id if it didn't have one
    if not original.series_id:
        original.series_id = series_id

    db.add(copy)
    db.commit()
    db.refresh(copy)

    return RedirectResponse(
        url=f"/admin/{copy.id}/{copy.creator_token}", status_code=303
    )


@router.post("/admin/{event_id}/{creator_token}/remover/{participant_id}")
def remove_participant(
    event_id: str,
    creator_token: str,
    participant_id: str,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    participant = db.query(Participant).filter(
        Participant.id == participant_id, Participant.event_id == event_id
    ).first()
    if participant:
        db.delete(participant)
        db.commit()

    return RedirectResponse(url=f"/admin/{event_id}/{creator_token}", status_code=303)


@router.post("/admin/{event_id}/{creator_token}/notif-leer")
def mark_notifications_read(
    event_id: str,
    creator_token: str,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    for n in event.notifications:
        n.read = True
    db.commit()

    return RedirectResponse(url=f"/admin/{event_id}/{creator_token}", status_code=303)


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_logged_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return render_template(request, "dashboard.html", user=user, events=user.events)


@router.post("/admin/{event_id}/{creator_token}/vincular")
def link_event_to_user(
    event_id: str,
    creator_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or event.creator_token != creator_token:
        raise HTTPException(404, "No encontrado")

    user = get_logged_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    event.creator_id = user.id
    db.commit()

    return RedirectResponse(url=f"/admin/{event_id}/{creator_token}", status_code=303)


@router.get("/e/{event_id}/ical")
def ical_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(404, "No encontrado")

    dt = event.date
    uid = f"{event.id}@picadito"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Picadito//ES",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND:{dt.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{event.title}",
        f"DESCRIPTION:{event.description}" if event.description else "DESCRIPTION:",
        f"LOCATION:{event.location}" if event.location else "",
        "END:VEVENT",
        "END:VCALENDAR",
    ]

    content = "\r\n".join([l for l in lines if l])

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{event.id}.ics"'},
    )
