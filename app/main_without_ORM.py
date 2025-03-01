import time
from typing import List, Optional

import mysql.connector
from fastapi import Body, FastAPI, HTTPException, Response, status
from pydantic import BaseModel

app = FastAPI()


def get_db_connection():
    """Get a connection to the MySQL database.

    This function will attempt to connect to the database with the given credentials
    indefinitely until a connection is established.

    Returns:
        mysql.connector.connection.MySQLConnection: A connection to the MySQL database
    """
    while True:
        try:
            conn = mysql.connector.connect(
                host="localhost", user="admin", password="Admin@123", database="mydb"
            )
            print("Database connection was successfull!")
            return conn
        except Exception as error:
            print("DB connection failed")
            print("Error : ", error)
            time.sleep(2)


# Models
class InputPost(BaseModel):
    title: str
    content: str
    published: Optional[bool]


class Post(BaseModel):
    id: int
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


# path operation or a route
@app.get("/")  # decorator
def check_working():
    """
    Simple route to check that the API is working.

    Returns:
        dict: A JSON response with a message.
    """
    return {"message": "hello world"}


# route to get posts
@app.get("/posts")
async def get_posts():
    """
    Get all posts.

    Returns:
        dict: A JSON response with a list of posts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Posts;")
    posts = cursor.fetchall()
    cursor.close()
    return {"data": posts}


@app.get("/posts/latest")
async def get_latest_post():
    """
    Get the latest post.

    Returns:
        dict: A JSON response with the latest post.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Posts ORDER BY modified_at DESC LIMIT 1;")
        post = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"data": post}
    except Exception as error:
        raise error


# path parameter
@app.get("/posts/{id}")
async def get_post(id: int):
    """
    Get a post by its id.

    Args:
        id (int): The id of the post to get.

    Returns:
        dict: A JSON response with the post if found, a 404 error otherwise.

    Raises:
        HTTPException: If the post is not found.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Posts where id = (%s);", (id,))
        post = cursor.fetchone()
        cursor.close()
        conn.close()
        if post:
            return {"data": post}
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id: {id} was not found",
        )
    except Exception as error:
        raise error


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post_data: InputPost = Body(...)):
    """
    Create a new post.

    Args:
        post_data (InputPost): The post to create.

    Returns:
        dict[str, Any]: A JSON response with the created post.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Posts (title, content, published) VALUES (%s, %s, %s)",
            (post_data.title, post_data.content, post_data.published),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return {
            "data": post_data.model_dump(),
            "message": "Post was successfully created",
        }

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the post: {error}",
        )


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_by_id(post_id: int):
    """Delete a post by its id."""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM Posts WHERE id = %s", (post_id,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with id {post_id} was not found",
            )

        conn.commit()

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the post: {error}",
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.put("/posts/{id}")
async def update_post(id: int, updated_post: InputPost = Body(...)) -> Response:
    """
    Update a post by its id.

    Args:
        id (int): The id of the post to update.
        updated_post (InputPost): The updated post data.

    Returns:
        Response: A response with status code 200 if the post is updated,
                  or raises a 404 error if the post is not found.

    Raises:
        HTTPException: If the post is not found.
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Posts SET title = %s, content = %s, published = %s WHERE id = %s;",
            (
                updated_post.title,
                updated_post.content,
                updated_post.published,
                id,
            ),
        )
        cursor.close()
        conn.close()
        return Response(
            status_code=status.HTTP_200_OK,
            headers={"message": f"post with id - {id} was successfully updated"},
        )
    except Exception as error:
        raise error
