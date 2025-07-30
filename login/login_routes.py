from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from login.schemas import UserCreate, UserLogin
from database.models import User
from database.database import get_db
from login.auth import hash_password, verify_password, create_token

# Add this if not already in auth.py
RESET_SECRET = "eclipse-reset-secret"
serializer = URLSafeTimedSerializer(RESET_SECRET)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

# ---------------- LOGIN ----------------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

    token = create_token({"sub": user.username})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie("access_token", token, httponly=True)
    return response

# ---------------- REGISTER ----------------

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_post(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    exists = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if exists:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username or email already taken"
        })

    new_user = User(
        full_name=full_name.strip(),
        username=username.strip(),
        email=email.strip(),
        password_hash=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=302)


# ---------------- FORGOT PASSWORD ----------------

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot-password.html", {"request": request})

@router.post("/forgot-password")
def forgot_password_post(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()

    # Send reset token only if user exists
    if user:
        token = serializer.dumps(user.email, salt="reset-salt")
        reset_url = f"http://localhost:8000/auth/reset-password?token={token}"
        print("RESET LINK:", reset_url) 

    return templates.TemplateResponse("forgot-password.html", {
        "request": request,
        "sent": True
    })

# ---------------- RESET PASSWORD ----------------

@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    try:
        serializer.loads(token, salt="reset-salt", max_age=3600)
        return templates.TemplateResponse("reset-password.html", {
            "request": request,
            "token": token
        })
    except (SignatureExpired, BadSignature):
        return templates.TemplateResponse("reset-password.html", {
            "request": request,
            "error": "Invalid or expired token"
        })

@router.post("/reset-password")
def reset_password_post(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        email = serializer.loads(token, salt="reset-salt", max_age=3600)
    except (SignatureExpired, BadSignature):
        return templates.TemplateResponse("reset-password.html", {
            "request": request,
            "error": "Invalid or expired token",
            "token": token  # important to re-render with token if partially working
        })

    if len(password) < 8:
        return templates.TemplateResponse("reset-password.html", {
            "request": request,
            "error": "Password must be at least 8 characters",
            "token": token
        })

    user = db.query(User).filter(User.email == email).first()
    if user:
        user.password_hash = hash_password(password)
        db.commit()

    return RedirectResponse("/auth/login", status_code=302)

# ---------------- LOGOUT ----------------

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response
