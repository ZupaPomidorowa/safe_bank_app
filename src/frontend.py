from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Cookie, Request, Response, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uuid

from src.database import DB

COOKIE = ''
USER = ''

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter()
db = DB()

def check_cookie(session_key):
    if session_key != COOKIE:
        return RedirectResponse("/error")
    
def check_password(password):
    if not (12 <= len(password) <= 64):
        return False
    return True

@router.get("/", include_in_schema=False)
def get_login(request: Request) -> Response:
    return templates.TemplateResponse("login.jinja2", {
        "request": request
    })

@router.post("/")
def post_login(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()]) -> Response:
    user = db.check_user(username, password)
    if user is False:
        return RedirectResponse("/error", status_code=301)
    
    global COOKIE
    COOKIE = str(uuid.uuid4())

    db.add_session(username, COOKIE)

    response = RedirectResponse("/dashboard", status_code=301)
    response.set_cookie(key="session", value=COOKIE, httponly=True)
    return response

@router.get("/error", include_in_schema=False)
def get_error(request: Request) -> Response:
    try:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except HTTPException as e:
        return templates.TemplateResponse("error.jinja2", {
            "request": request, 
            "error": e.detail}, 
            status_code=e.status_code)
    
@router.get("/logout", include_in_schema=False)
def get_logout(request: Request,  session : Annotated[str | None, Cookie()] = None) -> Response:
    db.delete_session(session)
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session")
    return response

@router.get("/dashboard", include_in_schema=False)
def get_dashboard(request: Request, session : Annotated[str | None, Cookie()] = None) -> Response:
    check_cookie(session)
    username = db.get_username(COOKIE)
    balance = db.get_balance(username)
    return templates.TemplateResponse("dashboard.jinja2", {
        "request": request,
        "username": username,
        "balance": balance,
    })

@router.get("/transferlist", include_in_schema=False)
def get_transferlist(request: Request, session : Annotated[str | None, Cookie()] = None) -> Response:
    check_cookie(session)
    username = db.get_username(COOKIE)
    headings = ("Date", "Title", "Category", "Amount", "From / To", "IBAN")
    rows = db.get_transfers(username)
    return templates.TemplateResponse("transferlist.jinja2", {
        "request": request,
        "headings": headings,
        "rows": rows,
    })

@router.get("/transfer", include_in_schema=False)
def get_transfer(request: Request, session : Annotated[str | None, Cookie()] = None) -> Response:
    check_cookie(session)
    username = db.get_username(COOKIE)
    return templates.TemplateResponse("transfer.jinja2", {
        "request": request,
    })

@router.post("/transfer", include_in_schema=False)
def post_transfer(
    request: Request,
    title: Annotated[str, Form()],
    amount: Annotated[int, Form()],
    recipient: Annotated[str, Form()],
    iban: Annotated[str, Form()],
    get_cookie_key: str | None = Cookie(None)
) -> Response:
    check_cookie(get_cookie_key)
    username = db.get_username(COOKIE)
    db.do_transfer(username, title, amount, recipient, iban)
    return RedirectResponse("/transfer", status_code=301)

@router.get("/data", include_in_schema=False)
def get_data(request: Request, session : Annotated[str | None, Cookie()] = None) -> Response:
    check_cookie(session)
    username = db.get_username(COOKIE)
    data = db.get_data(username)
    return templates.TemplateResponse("data.jinja2", {
        "request": request,
        "iban": data[0],
        "cardnum": data[1]
    })

@router.get("/passwordchange", include_in_schema=False)
def get_changepassword(request: Request, session : Annotated[str | None, Cookie()] = None) -> Response:
    check_cookie(session)
    message = {"text": '', "success": False}
    return templates.TemplateResponse("passwordchange.jinja2", {
        "request": request,
        "message": message,
    })

@router.post("/passwordchange", include_in_schema=False)
def post_changepassword(
    request: Request,
    old_pass: Annotated[str, Form()],
    new_pass1: Annotated[str, Form()],
    new_pass2: Annotated[str, Form()],
    session: str | None = Cookie(None)
) -> Response:
    check_cookie(session)
    username = db.get_username(COOKIE)
    message = {"text": '', "success": False}

    if db.verify_password(username, old_pass):
        if new_pass1 == new_pass2:
            if check_password(new_pass1):
                db.update_password(username, new_pass1)
                message["text"] = "Password changed successfully."
                message["success"] = True
            else:
                message["text"] = "Password must be 12-64 characters long"
        else:
            message["text"] = "New passwords don't match."
    else:
        message["text"] = "Incorrect password."


    return templates.TemplateResponse("passwordchange.jinja2", {
        "request": request,
        "message": message,
    })


