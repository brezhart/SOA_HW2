from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Query, Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import httpx
from typing import List, Optional

from schemas import (
    PostCreate, PostUpdate, Post, PaginatedPosts,
    PostViewResponse, PostLikeRequest, PostLikeResponse,
    CommentCreate, Comment, PaginatedComments
)
from grpc_client import PostServiceClient

app = FastAPI()
USER_SERVICE_URL = "http://user_service:8001"

post_service = PostServiceClient()

SECRET_KEY = "JOPAAAAAAAA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{login}")
    
    if response.status_code != 200:
        raise credentials_exception
    
    return response.json()

@app.post("/register")
async def register_proxy(user_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/register",
            json=user_data
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Registration failed")
        )
    
    user_data = response.json()
    
    return user_data

@app.post("/login")
async def login_proxy(credentials: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_SERVICE_URL}/login",
            json=credentials
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": credentials["login"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile")
async def get_profile_proxy(current_user: dict = Depends(get_current_user)):
    return current_user

@app.put("/profile")
async def update_profile_proxy(
    update_data: dict,
    current_user: dict = Depends(get_current_user)
):
    if "login" in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change login"
        )

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{USER_SERVICE_URL}/users/{current_user['login']}",
            json=update_data
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Update failed")
        )
    
    return response.json()

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/posts", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.create_post(
            title=post_data.title,
            description=post_data.description,
            creator_id=user_id,
            is_private=post_data.is_private,
            tags=post_data.tags
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/posts/{post_id}", response_model=Post)
async def get_post(
    post_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.get_post(post_id=post_id, user_id=user_id)
        
        return result
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        elif "Permission denied" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(
    post_data: PostUpdate,
    post_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.update_post(
            post_id=post_id,
            user_id=user_id,
            title=post_data.title,
            description=post_data.description,
            is_private=post_data.is_private,
            tags=post_data.tags
        )
        
        return result
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        elif "Permission denied" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        post_service.delete_post(post_id=post_id, user_id=user_id)
        
        return None
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        elif "Permission denied" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )

@app.get("/posts", response_model=PaginatedPosts)
async def list_posts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Extract user ID from the current user
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.list_posts(
            page=page,
            page_size=page_size,
            user_id=user_id
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/posts/{post_id}/view", response_model=PostViewResponse)
async def view_post(
    post_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.view_post(post_id=post_id, user_id=user_id)
        
        return result
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        elif "Permission denied" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )

@app.post("/posts/{post_id}/like", response_model=PostLikeResponse)
async def like_post(
    like_data: PostLikeRequest,
    post_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.like_post(
            post_id=post_id,
            user_id=user_id,
            is_like=like_data.is_like
        )
        
        return result
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        elif "Permission denied" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )

@app.post("/posts/{post_id}/comments", response_model=Comment)
async def create_comment(
    comment_data: CommentCreate,
    post_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.comment_post(
            post_id=post_id,
            user_id=user_id,
            content=comment_data.content
        )
        
        return result
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        elif "Permission denied" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )

@app.get("/posts/{post_id}/comments", response_model=PaginatedComments)
async def list_comments(
    post_id: int = Path(..., gt=0),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        result = post_service.list_comments(
            post_id=post_id,
            page=page,
            page_size=page_size
        )
        
        return result
    except Exception as e:
        error_message = str(e)
        
        if "Post not found" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )
