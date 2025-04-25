import grpc
from concurrent import futures
import time
from datetime import datetime
import math
from sqlalchemy.orm import Session
from sqlalchemy import desc
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty

from app import models, schemas, database
import post_pb2
import post_pb2_grpc

def get_db():
    db = database.SessionLocal()
    try:
        return db
    finally:
        db.close()

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos / 1e9)

def datetime_to_timestamp(dt):
    timestamp = Timestamp()
    timestamp.seconds = int(dt.timestamp())
    timestamp.nanos = int((dt.timestamp() - timestamp.seconds) * 1e9)
    return timestamp

class PostServicer(post_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        db = get_db()
        
        # Create new post
        new_post = models.Post(
            title=request.title,
            description=request.description,
            creator_id=request.creator_id,
            is_private=request.is_private,
            tags=list(request.tags),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        
        # Convert to gRPC response
        response = post_pb2.Post(
            id=new_post.id,
            title=new_post.title,
            description=new_post.description,
            creator_id=new_post.creator_id,
            is_private=new_post.is_private,
            tags=new_post.tags
        )
        
        response.created_at.CopyFrom(datetime_to_timestamp(new_post.created_at))
        response.updated_at.CopyFrom(datetime_to_timestamp(new_post.updated_at))
        
        return response
    
    def GetPost(self, request, context):
        db = get_db()
        
        # Get post by ID
        post = db.query(models.Post).filter(models.Post.id == request.id).first()

        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.id} not found")
            return post_pb2.Post()

        if post.is_private and post.creator_id != request.user_id:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("You don't have permission to access this post")
            return post_pb2.Post()
        
        response = post_pb2.Post(
            id=post.id,
            title=post.title,
            description=post.description,
            creator_id=post.creator_id,
            is_private=post.is_private,
            tags=post.tags
        )
        
        response.created_at.CopyFrom(datetime_to_timestamp(post.created_at))
        response.updated_at.CopyFrom(datetime_to_timestamp(post.updated_at))
        
        return response
    
    def UpdatePost(self, request, context):
        db = get_db()
        
        # Get post by ID
        post = db.query(models.Post).filter(models.Post.id == request.id).first()
        
        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.id} not found")
            return post_pb2.Post()

        if post.creator_id != request.user_id:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("You don't have permission to update this post")
            return post_pb2.Post()

        if request.title:
            post.title = request.title
        if request.description:
            post.description = request.description

        post.is_private = request.is_private

        if request.tags:
            post.tags = list(request.tags)

        post.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(post)

        response = post_pb2.Post(
            id=post.id,
            title=post.title,
            description=post.description,
            creator_id=post.creator_id,
            is_private=post.is_private,
            tags=post.tags
        )
        
        response.created_at.CopyFrom(datetime_to_timestamp(post.created_at))
        response.updated_at.CopyFrom(datetime_to_timestamp(post.updated_at))

        return response

    def DeletePost(self, request, context):
        db = get_db()


        post = db.query(models.Post).filter(models.Post.id == request.id).first()
        
        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.id} not found")
            return Empty()

        if post.creator_id != request.user_id:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("You don't have permission to delete this post")
            return Empty()

        db.delete(post)
        db.commit()

        return Empty()

    def ListPosts(self, request, context):
        db = get_db()

        query = db.query(models.Post)

        if request.user_id:
            query = query.filter(
                (models.Post.is_private == False) | 
                (models.Post.creator_id == request.user_id)
            )
        else:
            query = query.filter(models.Post.is_private == False)

        total_count = query.count()

        page = max(1, request.page)
        page_size = max(1, min(100, request.page_size))  # Limit page size
        total_pages = math.ceil(total_count / page_size)

        posts = query.order_by(desc(models.Post.created_at)) \
                    .offset((page - 1) * page_size) \
                    .limit(page_size) \
                    .all()

        response = post_pb2.ListPostsResponse(
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

        for post in posts:
            post_proto = post_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                is_private=post.is_private,
                tags=post.tags
            )
            
            post_proto.created_at.CopyFrom(datetime_to_timestamp(post.created_at))
            post_proto.updated_at.CopyFrom(datetime_to_timestamp(post.updated_at))

            response.posts.append(post_proto)

        return response

def serve():
    database.init_db()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_pb2_grpc.add_PostServiceServicer_to_server(PostServicer(), server)

    server.add_insecure_port('[::]:50051')
    server.start()
    
    print("Post gRPC server started on port 50051")
    
    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
