from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import DEBUG

app = FastAPI(debug=DEBUG)

app.add_middleware(SessionMiddleware, secret_key="picadito-secret-key-change-in-production")

from app.database import Base, engine
from app.models import User, Event, Participant, Notification
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent
tpl = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

from app.routers.web import router as web_router
from app.routers.auth import router as auth_router
app.include_router(web_router)
app.include_router(auth_router)
