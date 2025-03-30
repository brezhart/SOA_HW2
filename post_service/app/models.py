from sqlalchemy import Column, Integer, String, DateTime, Boolean, Table, ForeignKey, ARRAY
from sqlalchemy.sql import func
from app.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    creator_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    is_private = Column(Boolean, default=False)
    tags = Column(ARRAY(String), default=[])
