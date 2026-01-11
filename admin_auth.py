from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from DBadmin import SessionLocaladmin
from adminmodelsdb import Admin
from dotenv import load_dotenv
import os
# Configuration
load_dotenv()
SECRET_KEY = os.getenv("KunciAsu")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_admin_token(admin_id: int, username: str, is_super_admin: bool) -> str:
    payload = {
        "admin_id": admin_id,
        "username": username,
        "is_super_admin": is_super_admin,
        "type": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_admin_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid admin token"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Database dependency
def get_admin_db():
    db = SessionLocaladmin()
    try:
        yield db
    finally:
        db.close()

# Get current admin from token
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_admin_db)
) -> Admin:
    token = credentials.credentials
    payload = decode_admin_token(token)
    
    admin = db.query(Admin).filter(
        Admin.id == payload["admin_id"],
        Admin.is_active == True
    ).first()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found or inactive"
        )
    
    return admin

# Require super admin
async def get_super_admin(admin: Admin = Depends(get_current_admin)) -> Admin:
    if not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return admin