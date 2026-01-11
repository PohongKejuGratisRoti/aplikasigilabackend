from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./admintolol.db"

engineadmin = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocaladmin = sessionmaker(autocommit=False, autoflush=False, bind=engineadmin)
BaseAdmin = declarative_base() 