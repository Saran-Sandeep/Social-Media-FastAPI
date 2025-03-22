from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/votes", tags=["Votes"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[int, Depends(oauth2.get_current_user)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_vote(vote: schemas.Vote, db: DbSession, user_id: CurrentUser):
    try:
        post: models.Post | None = (
            db.query(models.Post).filter(models.Post.id == vote.post_id).first()
        )
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {vote.post_id} was not found",
            )

        existing_vote: models.Vote | None = (
            db.query(models.Vote)
            .filter(
                models.Vote.post_id == vote.post_id,
                models.Vote.user_id == user_id,
            )
            .first()
        )

        if vote.vote_dir:
            if existing_vote:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with id {user_id} have already voted on the post with id {vote.post_id}.",
                )

            new_vote = models.Vote(post_id=vote.post_id, user_id=user_id)
            db.add(new_vote)
            db.commit()
            db.refresh(new_vote)
        else:
            if not existing_vote:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Vote with post id {vote.post_id} and user id {user_id} was not found.",
                )

            db.delete(existing_vote)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=f"Vote with post id {vote.post_id} and user id {user_id} was deleted.",
            )

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the vote.",
        ) from error
