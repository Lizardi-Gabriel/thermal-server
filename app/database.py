from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Obtener las credenciales del archivo .env
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# crear el motor de la base de datos
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    echo=True,
    pool_pre_ping=True,
    connect_args={"ssl_disabled": True}
)

# crear la sesion
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# crear la base
Base = declarative_base()


# dependencia para obtener la sesion
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

