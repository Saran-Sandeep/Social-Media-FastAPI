from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import models
from .database import engine
from .routers import post, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables are created at startup."""
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(post.router)
app.include_router(user.router)


@app.get("/")
def root():
    return {"message": "Hello World"}
