from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from admin_auth import (
    get_admin_db, get_current_admin, get_super_admin,
    hash_password, verify_password, create_admin_token
)
from admin_schemas import (
    AdminCreate, AdminLogin, AdminResponse, AdminUpdate, 
    TokenResponse, AuditLogResponse
)
from adminmodelsdb import Admin, AdminAuditLog
from DBadmin import SessionLocaladmin  # ✅ ADD THIS IMPORT

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Helper function to log admin actions
def log_action(
    db: Session,
    admin_id: int,
    action: str,
    target_type: str = None,
    target_id: int = None,
    details: str = None,
    ip_address: str = None
):
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

# ============ AUTH ROUTES ============

@admin_router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(
    admin_data: AdminCreate,
    request: Request,
    db: Session = Depends(get_admin_db),
    current_admin: Admin = Depends(get_super_admin)
):
    # Check if username or email exists
    existing = db.query(Admin).filter(
        (Admin.username == admin_data.username) | (Admin.email == admin_data.email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create new admin
    new_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hash_password(admin_data.password),
        full_name=admin_data.full_name,
        is_super_admin=admin_data.is_super_admin
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    # Log action
    log_action(
        db, current_admin.id, "ADMIN_CREATED", "admin", new_admin.id,
        f"Created admin: {admin_data.username}", request.client.host
    )
    
    return new_admin

@admin_router.post("/login", response_model=TokenResponse)
async def admin_login(
    credentials: AdminLogin,
    request: Request,
    db: Session = Depends(get_admin_db)
):
    # Find admin
    admin = db.query(Admin).filter(
        Admin.username == credentials.username,
        Admin.is_active == True
    ).first()
    
    if not admin or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    admin.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Log action
    log_action(db, admin.id, "ADMIN_LOGIN", ip_address=request.client.host)
    
    # Create token
    token = create_admin_token(admin.id, admin.username, admin.is_super_admin)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": admin
    }

@admin_router.get("/me", response_model=AdminResponse)
async def get_me(admin: Admin = Depends(get_current_admin)):
    return admin

# ============ ADMIN MANAGEMENT ============

@admin_router.get("/all", response_model=List[AdminResponse])
async def get_all_admins(
    db: Session = Depends(get_admin_db),
    admin: Admin = Depends(get_super_admin)
):
    admins = db.query(Admin).all()
    return admins

@admin_router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    db: Session = Depends(get_admin_db),
    current_admin: Admin = Depends(get_current_admin)
):
    # Can view self or if super admin
    if current_admin.id != admin_id and not current_admin.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    
    return admin

@admin_router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    admin_update: AdminUpdate,
    request: Request,
    db: Session = Depends(get_admin_db),
    current_admin: Admin = Depends(get_current_admin)
):
    # Can update self or if super admin
    if current_admin.id != admin_id and not current_admin.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    
    # Update fields
    if admin_update.email:
        admin.email = admin_update.email
    if admin_update.full_name:
        admin.full_name = admin_update.full_name
    if admin_update.password:
        admin.hashed_password = hash_password(admin_update.password)
    
    db.commit()
    db.refresh(admin)
    
    # Log action
    log_action(
        db, current_admin.id, "ADMIN_UPDATED", "admin", admin_id,
        f"Updated admin: {admin.username}", request.client.host
    )
    
    return admin

@admin_router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    request: Request,
    db: Session = Depends(get_admin_db),
    current_admin: Admin = Depends(get_super_admin)
):
    if current_admin.id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    
    username = admin.username
    db.delete(admin)
    db.commit()
    
    # Log action
    log_action(
        db, current_admin.id, "ADMIN_DELETED", "admin", admin_id,
        f"Deleted admin: {username}", request.client.host
    )
    
    return {"message": f"Admin {admin_id} deleted successfully"}

# ============ AUDIT LOGS ============

@admin_router.get("/audit-logs/all", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_admin_db),
    admin: Admin = Depends(get_super_admin)
):
    logs = db.query(AdminAuditLog).order_by(
        AdminAuditLog.created_at.desc()
    ).limit(limit).all()
    
    return logs

# ============ USER MANAGEMENT ROUTES (Managing useranjing.db) ============

from DbLogin import SessionLocal  # Import regular user DB
import modelsDB  # Import regular user models

def get_user_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@admin_router.get("/users/all")
async def get_all_users(
    db: Session = Depends(get_user_db),  # Uses useranjing.db
    admin: Admin = Depends(get_current_admin)  # Checks admin from admintolol.db
):
    users = db.query(modelsDB.User).all()
    return {"users": users, "total": len(users)}

@admin_router.get("/users/{user_id}")
async def get_user_detail(
    user_id: int,
    db: Session = Depends(get_user_db),
    admin: Admin = Depends(get_current_admin)
):
    user = db.query(modelsDB.User).filter(modelsDB.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"user": user}

@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_user_db),
    admin: Admin = Depends(get_current_admin)
):
    user = db.query(modelsDB.User).filter(modelsDB.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    username = user.username
    db.delete(user)
    db.commit()
    
    # Log action in admin DB
    admin_db = SessionLocaladmin()
    log_action(
        admin_db, admin.id, "USER_DELETED", "user", user_id,
        f"Deleted user: {username}", request.client.host
    )
    admin_db.close()
    
    return {"message": f"User {username} deleted successfully"}

@admin_router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    request: Request,
    db: Session = Depends(get_user_db),
    admin: Admin = Depends(get_current_admin)
):
    user = db.query(modelsDB.User).filter(modelsDB.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Assuming you have an is_active field, if not you can add it
    # user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User {user.username} status updated"}

@admin_router.get("/users/{user_id}/locations")
async def get_user_locations(
    user_id: int,
    db: Session = Depends(get_user_db),
    admin: Admin = Depends(get_current_admin)
):
    # Assuming you have a UserLocation model
    locations = db.query(modelsDB.UserLocation).filter(
        modelsDB.UserLocation.user_id == user_id
    ).order_by(modelsDB.UserLocation.updated_at.desc()).limit(50).all()
    
    return {"user_id": user_id, "locations": locations}