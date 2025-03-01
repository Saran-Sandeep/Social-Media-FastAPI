from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas, utils
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[schemas.UserOut])
def read_users(db: Session = Depends(get_db)) -> List[schemas.UserOut]:
    """Get all users."""
    users: list[models.User] = db.query(models.User).all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found",
        )

    return [schemas.UserOut.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=schemas.UserOut)
def read_user_by_id(user_id: int, db: Session = Depends(get_db)) -> schemas.UserOut:
    """Get a user by its ID."""
    user: models.User | None = (
        db.query(models.User).filter(models.User.id == user_id).first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found",
        )

    return schemas.UserOut.model_validate(user)


# check username and email are unique
def unique_user(username: str, email: str, db: Session) -> bool:

    existing_user: models.User | None = (
        db.query(models.User)
        .filter(or_(models.User.username == username, models.User.email == email))
        .first()
    )

    if existing_user:
        if existing_user.username == username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        if existing_user.email == email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

    return True


# creating an user
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(
    user: schemas.InputUser, db: Session = Depends(get_db)
) -> schemas.UserOut:

    try:
        unique_user(user.username, user.email, db)
        hashed_password: str = utils.hash(user.password)
        user.password = hashed_password
        new_user = models.User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user.",
        ) from error

    return schemas.UserOut.model_validate(new_user)
