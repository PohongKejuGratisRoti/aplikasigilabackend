from datetime import timedelta, datetime
from typing import Annotated
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from DbLogin import SessionLocal
from modelsDB import User 
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from fastapi import APIRouter


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)