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
    prefix="/auth",
    tags=["auth"],
)

load_dotenv()
SECRET_KEY = os.getenv("KunciJembot")
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    username: str
    password: str  

class Token(BaseModel):
    access_token: str
    token_type: str


def get_dbuser():
    dbuser = SessionLocal()
    try:
        yield dbuser
    finally:
        dbuser.close()

db_dependency = Annotated[Session, Depends(get_dbuser)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user( create_user_request: CreateUserRequest,dbuser: db_dependency):


    create_user_model = User(
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password)
    )

    dbuser.add(create_user_model)
    dbuser.commit()

def authenticate_user(username: str, password: str, dbuser: Session):
    user = dbuser.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta | None = None):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)



@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], dbuser: db_dependency):

    user = authenticate_user(form_data.username, form_data.password, dbuser)
    token = create_access_token(user.username, user.id, timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")