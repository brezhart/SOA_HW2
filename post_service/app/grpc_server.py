import grpc
from concurrent import futures
import time
from datetime import datetime
import math
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty
from sqlalchemy.exc import IntegrityError

from app import models, schemas, database
from app.kafka_producer import kafka_client
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

def get_post_counts(db, post_id):
    """Get the views, likes, and comments counts for a post"""
    views_count = db.query(func.count(models.PostView.id)).filter(models.PostView.post_id == post_id).scalar()
    likes_count = db.query(func.count(models.PostLike.id)).filter(models.PostLike.post_id == post_id).scalar()
    comments_count = db.query(func.count(models.PostComment.id)).filter(models.PostComment.post_id == post_id).scalar()
    
    return views_count, likes_count, comments_count

def populate_post_response(post, db=None):
    """Populate a post response with counts"""
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
    
    # Add counts if db is provided
    if db:
        views_count, likes_count, comments_count = get_post_counts(db, post.id)
        response.views_count = views_count
        response.likes_count = likes_count
        response.comments_count = comments_count
    else:
        # Use the values from the post object (which might be 0 if not populated)
        response.views_count = post.views_count
        response.likes_count = post.likes_count
        response.comments_count = post.comments_count
    
    return response

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
        response = populate_post_response(new_post, db)
        
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
        
        response = populate_post_response(post, db)
        
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

        # Convert to gRPC response
        response = populate_post_response(post, db)

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
            post_proto = populate_post_response(post, db)
            response.posts.append(post_proto)

        return response
    
    def ViewPost(self, request, context):
        db = get_db()
        
        # Get post by ID
        post = db.query(models.Post).filter(models.Post.id == request.post_id).first()
        
        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.post_id} not found")
            return post_pb2.ViewPostResponse()
        
        if post.is_private and post.creator_id != request.user_id:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("You don't have permission to view this post")
            return post_pb2.ViewPostResponse()
        
        try:
            existing_view = db.query(models.PostView).filter(
                models.PostView.post_id == request.post_id,
                models.PostView.user_id == request.user_id
            ).first()
            
            if not existing_view:
                # Create a new view record
                view_time = datetime.utcnow()
                new_view = models.PostView(
                    post_id=request.post_id,
                    user_id=request.user_id,
                    viewed_at=view_time
                )
                
                db.add(new_view)
                db.commit()
                
                # Send event to Kafka
                kafka_client.send_post_view_event(
                    user_id=request.user_id,
                    post_id=request.post_id,
                    view_date=view_time
                )
            
            views_count = db.query(func.count(models.PostView.id)).filter(
                models.PostView.post_id == request.post_id
            ).scalar()
            
            return post_pb2.ViewPostResponse(
                success=True,
                views_count=views_count
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error recording view: {str(e)}")
            return post_pb2.ViewPostResponse(success=False, views_count=0)
    
    def LikePost(self, request, context):
        db = get_db()
        
        # Get post by ID
        post = db.query(models.Post).filter(models.Post.id == request.post_id).first()
        
        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.post_id} not found")
            return post_pb2.LikePostResponse()
        
        if post.is_private and post.creator_id != request.user_id:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("You don't have permission to like this post")
            return post_pb2.LikePostResponse()
        
        try:
            # Check if the user has already liked this post
            existing_like = db.query(models.PostLike).filter(
                models.PostLike.post_id == request.post_id,
                models.PostLike.user_id == request.user_id
            ).first()
            
            like_time = datetime.utcnow()
            
            if request.is_like:
                if not existing_like:
                    new_like = models.PostLike(
                        post_id=request.post_id,
                        user_id=request.user_id,
                        created_at=like_time
                    )
                    
                    db.add(new_like)
                    db.commit()
                    
                    # Send event to Kafka
                    kafka_client.send_post_like_event(
                        user_id=request.user_id,
                        post_id=request.post_id,
                        like_date=like_time,
                        is_like=True
                    )
            else:
                if existing_like:
                    db.delete(existing_like)
                    db.commit()
                    
                    kafka_client.send_post_like_event(
                        user_id=request.user_id,
                        post_id=request.post_id,
                        like_date=like_time,
                        is_like=False
                    )
            
            likes_count = db.query(func.count(models.PostLike.id)).filter(
                models.PostLike.post_id == request.post_id
            ).scalar()
            
            is_liked = db.query(models.PostLike).filter(
                models.PostLike.post_id == request.post_id,
                models.PostLike.user_id == request.user_id
            ).first() is not None
            
            return post_pb2.LikePostResponse(
                success=True,
                likes_count=likes_count,
                is_liked=is_liked
            )
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error processing like: {str(e)}")
            return post_pb2.LikePostResponse(success=False, likes_count=0, is_liked=False)
    
    def CommentPost(self, request, context):
        db = get_db()
        
        post = db.query(models.Post).filter(models.Post.id == request.post_id).first()
        
        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.post_id} not found")
            return post_pb2.Comment()
        
        if post.is_private and post.creator_id != request.user_id:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("You don't have permission to comment on this post")
            return post_pb2.Comment()
        
        try:
            comment_time = datetime.utcnow()
            new_comment = models.PostComment(
                post_id=request.post_id,
                user_id=request.user_id,
                content=request.content,
                created_at=comment_time
            )
            
            db.add(new_comment)
            db.commit()
            db.refresh(new_comment)
            
            kafka_client.send_post_comment_event(
                user_id=request.user_id,
                post_id=request.post_id,
                comment_id=new_comment.id,
                comment_date=comment_time
            )
            
            response = post_pb2.Comment(
                id=new_comment.id,
                post_id=new_comment.post_id,
                user_id=new_comment.user_id,
                content=new_comment.content
            )
            
            response.created_at.CopyFrom(datetime_to_timestamp(new_comment.created_at))
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error creating comment: {str(e)}")
            return post_pb2.Comment()
    
    def ListComments(self, request, context):
        db = get_db()
        
        post = db.query(models.Post).filter(models.Post.id == request.post_id).first()
        
        if not post:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Post with ID {request.post_id} not found")
            return post_pb2.ListCommentsResponse()
        
        if post.is_private:
            pass
        
        query = db.query(models.PostComment).filter(models.PostComment.post_id == request.post_id)
        
        total_count = query.count()
        
        page = max(1, request.page)
        page_size = max(1, min(100, request.page_size))  # Limit page size
        total_pages = math.ceil(total_count / page_size)
        
        comments = query.order_by(desc(models.PostComment.created_at)) \
                      .offset((page - 1) * page_size) \
                      .limit(page_size) \
                      .all()
        
        response = post_pb2.ListCommentsResponse(
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
        for comment in comments:
            comment_proto = post_pb2.Comment(
                id=comment.id,
                post_id=comment.post_id,
                user_id=comment.user_id,
                content=comment.content
            )
            
            comment_proto.created_at.CopyFrom(datetime_to_timestamp(comment.created_at))
            
            response.comments.append(comment_proto)
        
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
