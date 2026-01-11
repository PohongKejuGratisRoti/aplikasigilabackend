from fastapi import FastAPI, status, Depends, HTTPException
import modelsDB as modelsDB
from DbLogin import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
import auth
from auth import get_current_user
from location import router as location_router
from admin_routes import admin_router  # ✅ Make sure this line is here

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(location_router)
app.include_router(admin_router)  # ✅ Make sure this line is here

modelsDB.Base.metadata.create_all(bind=engine)

def get_dbuser():
    dbuser = SessionLocal()
    try:
        yield dbuser
    finally:
        dbuser.close()

dbuser_dependency = Annotated[Session, Depends(get_dbuser)]
user_dependency = Annotated[modelsDB.User, Depends(get_current_user)]

@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, dbuser: dbuser_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='server tolol gagal autentikasi')
    return {"User": user}



@app.post("/force-fun")
def force_fun():
    db = SessionLocal()
    try:
        users = db.query(modelsDB.User).all()
        touched = 0

        for user in users:
            if not user.fun_records:
                fun = modelsDB.FunRecord(
                    user_id=user.id,
                    funactivity=0,
                    funlevel=10
                )
                db.add(fun)
                touched += 1
            else:
                for record in user.fun_records:
                    record.funlevel = 10
                    touched += 1

        db.commit()

        return {
            "message": "Everyone has fun level 10 now",
            "records_updated": touched
        }
    finally:
        db.close()