from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from . import database, schemas
from .config import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_access_token(token: str, credentials_exception) -> schemas.TokenData:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        id: str = payload.get("sub")

        if id is None:
            raise credentials_exception

        token_data = schemas.TokenData(id=id)

    except InvalidTokenError:
        raise credentials_exception

    return token_data


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # token_data: schemas.TokenData = verify_access_token(token, credentials_exception)
    # user: models.User = (
    #     db.query(models.User).filter(models.User.id == token_data.id).first()
    # )
    # return user
    return int(verify_access_token(token, credentials_exception).id)
