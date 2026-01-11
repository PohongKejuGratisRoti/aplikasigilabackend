from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class AdminBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class AdminCreate(AdminBase):
    password: str
    is_super_admin: Optional[bool] = False

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(AdminBase):
    id: int
    is_super_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin: AdminResponse

class AuditLogResponse(BaseModel):
    id: int
    admin_id: Optional[int]
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True