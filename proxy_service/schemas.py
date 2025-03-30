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

class PaginatedPosts(BaseModel):
    posts: List[Post]
    total_count: int
    page: int
    page_size: int
    total_pages: int
