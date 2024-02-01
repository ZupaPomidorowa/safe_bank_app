from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Cookie, Request, Response, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uuid

from src.database import DB

COOKIE = ''
USER = ''
LETTER_NUM = ''

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
def get_home(request: Request) -> Response:
    return templates.TemplateResponse("home.jinja2", {
        "request": request
    })

@router.get("/login", include_in_schema=False)
def get_login(request: Request) -> Response:
    return templates.TemplateResponse("login.jinja2", {
        "request": request
    })

@router.post("/login")
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

@router.get("/login2", include_in_schema=False)
def get_login2(request: Request) -> Response:
    return templates.TemplateResponse("login2.jinja2", {
        "request": request
    })

@router.post("/login2")
def post_login(request: Request, username: Annotated[str, Form()]) -> Response:
    response = RedirectResponse("/processlogin", status_code=301)
    global USER 
    USER = username
    return response

@router.get("/processlogin", include_in_schema=False)
def get_processlogin(request: Request) -> Response:
    global LETTER_NUM
    LETTER_NUM = db.get_letternum(USER)

    return templates.TemplateResponse("processlogin.jinja2", {
        "request": request,
        "letter_num": LETTER_NUM,
    })

@router.post("/processlogin")
def post_processlogin(request: Request, 
                      letter1: Annotated[str, Form()], 
                      letter2: Annotated[str, Form()], 
                      letter3: Annotated[str, Form()], 
                      letter4: Annotated[str, Form()], 
                      letter5: Annotated[str, Form()]) -> Response:
    
    user = db.check_username(USER)
    if user is False:
        return RedirectResponse("/error", status_code=301)
    
    letters = letter1 + letter2 + letter3 + letter4 + letter5
    hash = db.check_hash(letters, USER, LETTER_NUM)
    if hash is False:
        return RedirectResponse("/error", status_code=301)
    
    global COOKIE
    COOKIE = str(uuid.uuid4())

    db.add_session(USER, COOKIE)

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


'''
def check_password(password):
    if not (12 <= len(password) <= 64):
        return False

    if not any(char.isupper() for char in password):
        return False

    if not any(char.isdigit() for char in password):
        return False

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True

@router.post("/passwordchange", include_in_schema=False)
def post_changepassword(
    request: Request,
    old_pass: Annotated[str, Form()],
    new_pass1: Annotated[str, Form()],
    new_pass2: Annotated[str, Form()],
    get_cookie_key: str | None = Cookie(None)
) -> Response:
    check_cookie(get_cookie_key)
    username = db.get_username(COOKIE)
    message = {"text": '', "success": False}

    if db.verify_password(username, old_pass):
        if new_pass1 == new_pass2:
            if check_password(new_pass1):
                db.update_password(username, new_pass1)
                message["text"] = "Password changed successfully."
                message["success"] = True
            else:
                message["text"] = "Password must be 12-64 characters long, must contain at least 1 uppercase letter, 1 number, and 1 special character."
        else:
            message["text"] = "New passwords don't match."
    else:
        message["text"] = "Incorrect password."


    return templates.TemplateResponse("password_change.jinja2", {
        "request": request,
        "message": message,
    })
'''
