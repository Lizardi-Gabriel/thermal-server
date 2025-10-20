from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app import crud, models, schemas
from app.database import get_db


# TODO: Cambiar estos valores por variables de entorno en producción
SECRET_KEY = "supersecreto"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10000

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# autenticación en la URL "/token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hashear_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Error hasheando contraseña: {e}")
        raise


def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """ Decodifica el token, extrae el nombre de usuario y lo busca en la BD. """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(nombre_usuario=username)
    except JWTError:
        raise credentials_exception

    usuario = crud.get_user_by_username(db, nombre_usuario=token_data.nombre_usuario)
    if usuario is None:
        raise credentials_exception
    return usuario