from DBadmin import engineadmin, BaseAdmin
from adminmodelsdb import Admin
from admin_auth import hash_password
from sqlalchemy.orm import Session

def init_admin_db():
    # Create tables
    BaseAdmin.metadata.create_all(bind=engineadmin)
    print("✅ Admin tables created")
    
    # Create super admin if not exists
    from DBadmin import SessionLocaladmin
    db = SessionLocaladmin()
    
    existing_admin = db.query(Admin).filter(Admin.username == "superadmin").first()
    
    if not existing_admin:
        super_admin = Admin(
            username="superadmin",
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            full_name="Super Administrator",
            is_super_admin=True,
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        print("✅ Super admin created")
        print("   Username: superadmin")
        print("   Password: admin123")
        print("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
    else:
        print("ℹ️  Super admin already exists")
    
    db.close()

if __name__ == "__main__":
    init_admin_db()