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

class PostInDB(PostBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime
    views_count: int = 0
    likes_count: int = 0
    comments_count: int = 0

    class Config:
        orm_mode = True
        from_attributes = True

class PostResponse(PostInDB):
    pass

class PaginatedPostResponse(BaseModel):
    posts: List[PostResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

# New schemas for post views, likes, and comments

class PostViewCreate(BaseModel):
    post_id: int
    user_id: int

class PostViewResponse(BaseModel):
    success: bool
    views_count: int

class PostLikeCreate(BaseModel):
    post_id: int
    user_id: int
    is_like: bool = True  # True for like, False for unlike

class PostLikeResponse(BaseModel):
    success: bool
    likes_count: int
    is_liked: bool

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)

class CommentCreate(CommentBase):
    post_id: int
    user_id: int

class CommentInDB(CommentBase):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class CommentResponse(CommentInDB):
    pass

class PaginatedCommentResponse(BaseModel):
    comments: List[CommentResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

# Kafka event schemas

class UserRegistrationEvent(BaseModel):
    user_id: int
    registration_date: datetime

class PostViewEvent(BaseModel):
    user_id: int
    post_id: int
    view_date: datetime

class PostLikeEvent(BaseModel):
    user_id: int
    post_id: int
    like_date: datetime
    is_like: bool  # True for like, False for unlike

class PostCommentEvent(BaseModel):
    user_id: int
    post_id: int
    comment_id: int
    comment_date: datetime
