from DbLogin import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime, timezone

class User(Base):
    __tablename__='users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

    location = relationship(
        "UserLocation",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    fun_records = relationship(
        "FunRecord",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserLocation(Base):
    __tablename__='userlocations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    latitude = Column(Float)
    longitude = Column(Float)
    updated_at = Column(
    DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    user = relationship("User", back_populates="location")


class FunRecord(Base):
    __tablename__='fun_records'

    idfun = Column(Integer, primary_key=True, index=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    funactivity = Column(Float)
    funlevel = Column(Integer)

    user = relationship("User", back_populates="fun_records")
