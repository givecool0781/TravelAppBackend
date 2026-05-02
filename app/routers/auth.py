import uuid
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from .. import models, schemas
from ..auth import hash_password, verify_password, create_token, get_current_user
from ..database import get_db
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory reset codes: {email: (code, expiry)}
_reset_codes: Dict[str, Tuple[str, float]] = {}

def _send_reset_email(to_email: str, code: str) -> bool:
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        print(f"[DEV] Reset code for {to_email}: {code}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "旅行規劃 APP — 重設密碼"
        msg["From"] = f"旅行規劃 <{settings.GMAIL_USER}>"
        msg["To"] = to_email
        html = f"""
        <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:24px">
          <h2 style="color:#0F172A">重設密碼</h2>
          <p style="color:#64748B">你的驗證碼是：</p>
          <h1 style="letter-spacing:12px;color:#2563EB;font-size:36px">{code}</h1>
          <p style="color:#94A3B8;font-size:13px">此驗證碼 1 小時內有效，請勿分享給他人。</p>
        </div>
        """
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            server.sendmail(settings.GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")
        return False

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=schemas.TokenResponse, status_code=201)
def register(body: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == body.email).first():
        raise HTTPException(status_code=400, detail="此 Email 已被註冊")
    user = models.User(id=str(uuid.uuid4()), email=body.email, password=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"access_token": create_token(user.id)}

@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Email 或密碼錯誤")
    return {"access_token": create_token(user.id)}

@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user

class ForgotRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
def forgot_password(body: ForgotRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    # 不透露帳號是否存在
    if user:
        code = f"{random.randint(0, 999999):06d}"
        _reset_codes[body.email] = (code, time.time() + 3600)
        _send_reset_email(body.email, code)
    return {"message": "若此 Email 有帳號，驗證碼已寄出"}

class ResetRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

@router.post("/reset-password")
def reset_password(body: ResetRequest, db: Session = Depends(get_db)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="密碼至少 8 個字元")

    entry = _reset_codes.get(body.email)
    if not entry or time.time() > entry[1] or entry[0] != body.code:
        raise HTTPException(status_code=400, detail="驗證碼錯誤或已過期")

    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到此帳號")

    user.password = hash_password(body.new_password)
    db.commit()
    del _reset_codes[body.email]
    return {"message": "密碼重設成功"}

class AdminResetRequest(BaseModel):
    admin_key: str
    email: EmailStr
    new_password: str

@router.post("/admin-reset")
def admin_reset(body: AdminResetRequest, db: Session = Depends(get_db)):
    if body.admin_key != settings.JWT_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到此帳號")
    user.password = hash_password(body.new_password)
    db.commit()
    return {"message": "密碼已重設"}
