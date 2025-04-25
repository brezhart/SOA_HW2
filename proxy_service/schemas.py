from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    is_private: bool = False
    tags: List[str] = []

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_private: Optional[bool] = None
    tags: Optional[List[str]] = None

class Post(PostBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0

class PaginatedPosts(BaseModel):
    posts: List[Post]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class PostViewResponse(BaseModel):
    success: bool
    views_count: int

class PostLikeRequest(BaseModel):
    is_like: bool = True

class PostLikeResponse(BaseModel):
    success: bool
    likes_count: int
    is_liked: bool

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)

class Comment(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime

class PaginatedComments(BaseModel):
    comments: List[Comment]
    total_count: int
    page: int
    page_size: int
    total_pages: int
