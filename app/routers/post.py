from typing import Annotated, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session

from .. import models, oauth2, schemas
from ..database import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[int, Depends(oauth2.get_current_user)]


@router.get("/", response_model=list[schemas.PostOut])
def read_posts(
    db: DbSession,
    user_id: CurrentUser,
    limit: int = 10,
    offset: int = 0,
    search: Optional[str] = "",
) -> list[schemas.PostOut]:
    """Get all posts."""
    posts: list[Row[Tuple[models.Post, int]]] = (
        db.query(models.Post, func.count(models.Vote.post_id).label("likes"))
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.title.contains(search))
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No posts found",
        )

    return [
        schemas.PostOut(
            **schemas.Post.model_validate(post, from_attributes=True).model_dump(),
            likes=likes,
        )
        for post, likes in posts
    ]


@router.get("/myposts", response_model=list[schemas.PostOut])
def read_user_posts(db: DbSession, user_id: CurrentUser) -> list[schemas.PostOut]:
    """Get all posts."""
    posts: list[Row[Tuple[models.Post, int]]] = (
        db.query(models.Post, func.count(models.Vote.post_id).label("likes"))
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.user_id == user_id)
        .all()
    )

    if not posts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No posts found",
        )

    return [
        schemas.PostOut(
            **schemas.Post.model_validate(post, from_attributes=True).model_dump(),
            likes=likes,
        )
        for post, likes in posts
    ]


@router.get("/{post_id}", response_model=schemas.PostOut)
def read_post_by_id(
    post_id: int, db: DbSession, user_id: CurrentUser
) -> schemas.PostOut:
    """Get a post by its ID."""
    post: Row[Tuple[models.Post, int]] | None = (
        db.query(models.Post, func.count(models.Vote.post_id).label("likes"))
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)
        .group_by(models.Post.id)
        .filter(models.Post.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} was not found",
        )

    post_obj: models.Post = post[0]
    likes: int = post[1]

    if post_obj.published:
        return schemas.PostOut(
            **schemas.Post.model_validate(post_obj, from_attributes=True).model_dump(),
            likes=likes,
        )

    if not post_obj.published and post_obj.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this post",
        )

    return schemas.PostOut(
        **schemas.Post.model_validate(post_obj, from_attributes=True).model_dump(),
        likes=likes,
    )


@router.post("/", response_model=schemas.Post, status_code=status.HTTP_201_CREATED)
def create_post(
    post: schemas.InputPost,
    db: DbSession,
    user_id: CurrentUser,
) -> schemas.Post:
    """Create a new post."""
    try:
        new_post = models.Post(**post.model_dump(), user_id=user_id)
        db.add(new_post)
        db.commit()
        db.refresh(new_post)

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the post.",
        ) from error

    return schemas.Post.model_validate(new_post, from_attributes=True)


@router.put("/{post_id}", response_model=schemas.Post)
def update_post(
    post_id: int, post: schemas.InputPost, db: DbSession, user_id: CurrentUser
) -> schemas.Post:
    """Update a post by its ID."""
    try:
        db_post: models.Post | None = (
            db.query(models.Post).filter(models.Post.id == post_id).first()
        )

        if db_post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} was not found",
            )

        if db_post.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this post",
            )

        # Update only provided fields
        for key, value in post.model_dump(exclude_unset=True).items():
            setattr(db_post, key, value)

        # db_post.modified_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(db_post)

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the post.",
        ) from error

    return schemas.Post.model_validate(db_post, from_attributes=True)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_by_id(post_id: int, db: DbSession, user_id: CurrentUser) -> None:
    """Delete a post by its id."""
    try:
        db_post: models.Post | None = (
            db.query(models.Post).filter(models.Post.id == post_id).first()
        )

        if db_post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {post_id} was not found",
            )

        if db_post.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this post.",
            )

        db.delete(db_post)
        db.commit()

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()
        print(error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the post.",
        ) from error

    return None
