# location.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Annotated
from datetime import datetime, timezone
from DbLogin import SessionLocal
from modelsDB import UserLocation, User
from auth import get_current_user

router = APIRouter(
    prefix="/location",
    tags=["location"],
)

def get_dbuser():
    dbuser = SessionLocal()
    try:
        yield dbuser
    finally:
        dbuser.close()

db_dependency = Annotated[Session, Depends(get_dbuser)]

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

class UserLocationOut(BaseModel):
    user_id: int
    latitude: float
    longitude: float
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/update")
def update_location(
    data: LocationUpdate,
    current_user: dict = Depends(get_current_user),  # Changed from user: User
    db: Session = Depends(get_dbuser)
):
    # Extract user_id from the dict
    user_id = current_user.get('id') or current_user.get('user_id')
    
    loc = db.query(UserLocation).filter_by(user_id=user_id).first()
    if loc:
        loc.latitude = data.latitude
        loc.longitude = data.longitude
        loc.updated_at = datetime.now(timezone.utc)
    else:
        loc = UserLocation(
            user_id=user_id,
            latitude=data.latitude,
            longitude=data.longitude
        )
        db.add(loc)
    db.commit()
    return {"status": "location updated"}

@router.get("/alllocations", response_model=List[UserLocationOut])
def get_all_locations(
    current_user: dict = Depends(get_current_user),  # Changed from user: User
    db: Session = Depends(get_dbuser)
):
    return db.query(UserLocation).all()