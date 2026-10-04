from __future__ import annotations

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "modelledger")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
elif DB_HOST and DB_USER:
    DATABASE_URL = (
        f"mysql+mysqlconnector://"
        f"{quote_plus(DB_USER)}:"
        f"{quote_plus(DB_PASSWORD)}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    DATABASE_URL = "sqlite:///./modelledger.db"


class Base(DeclarativeBase):
    pass


engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_recycle": 3600,
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)

if DATABASE_URL.startswith("sqlite"):
    sqlite_path = DATABASE_URL.replace("sqlite:///", "", 1)
    if sqlite_path and sqlite_path != ":memory:":
        resolved_path = os.path.abspath(os.path.join(os.path.dirname(__file__), sqlite_path))
        os.makedirs(os.path.dirname(resolved_path), exist_ok=True)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()