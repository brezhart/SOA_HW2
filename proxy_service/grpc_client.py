import grpc
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp

import post_pb2
import post_pb2_grpc

class PostServiceClient:
    def __init__(self, host="post_service:50051"):
        self.channel = grpc.insecure_channel(host)
        self.stub = post_pb2_grpc.PostServiceStub(self.channel)
    
    def timestamp_to_datetime(self, timestamp):
        return datetime.fromtimestamp(timestamp.seconds + timestamp.nanos / 1e9)
    
    def post_proto_to_dict(self, post_proto):
        return {
            "id": post_proto.id,
            "title": post_proto.title,
            "description": post_proto.description,
            "creator_id": post_proto.creator_id,
            "created_at": self.timestamp_to_datetime(post_proto.created_at),
            "updated_at": self.timestamp_to_datetime(post_proto.updated_at),
            "is_private": post_proto.is_private,
            "tags": list(post_proto.tags),
            "views_count": post_proto.views_count,
            "likes_count": post_proto.likes_count,
            "comments_count": post_proto.comments_count
        }
    
    def comment_proto_to_dict(self, comment_proto):
        return {
            "id": comment_proto.id,
            "post_id": comment_proto.post_id,
            "user_id": comment_proto.user_id,
            "content": comment_proto.content,
            "created_at": self.timestamp_to_datetime(comment_proto.created_at)
        }
    
    def create_post(self, title, description, creator_id, is_private=False, tags=None):
        if tags is None:
            tags = []
        
        request = post_pb2.CreatePostRequest(
            title=title,
            description=description,
            creator_id=creator_id,
            is_private=is_private,
            tags=tags
        )
        
        try:
            response = self.stub.CreatePost(request)
            return self.post_proto_to_dict(response)
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            raise Exception(f"gRPC error: {status_code}, {details}")
    
    def get_post(self, post_id, user_id):
        request = post_pb2.GetPostRequest(
            id=post_id,
            user_id=user_id
        )
        
        try:
            response = self.stub.GetPost(request)
            return self.post_proto_to_dict(response)
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            elif status_code == grpc.StatusCode.PERMISSION_DENIED:
                raise Exception(f"Permission denied: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
    
    def update_post(self, post_id, user_id, title=None, description=None, is_private=None, tags=None):
        request = post_pb2.UpdatePostRequest(
            id=post_id,
            user_id=user_id
        )
        
        if title is not None:
            request.title = title
        if description is not None:
            request.description = description
        if is_private is not None:
            request.is_private = is_private
        if tags is not None:
            request.tags.extend(tags)
        
        try:
            response = self.stub.UpdatePost(request)
            return self.post_proto_to_dict(response)
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            elif status_code == grpc.StatusCode.PERMISSION_DENIED:
                raise Exception(f"Permission denied: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
    
    def delete_post(self, post_id, user_id):
        request = post_pb2.DeletePostRequest(
            id=post_id,
            user_id=user_id
        )
        
        try:
            self.stub.DeletePost(request)
            return {"message": "Post deleted successfully"}
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            elif status_code == grpc.StatusCode.PERMISSION_DENIED:
                raise Exception(f"Permission denied: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
    
    def list_posts(self, page=1, page_size=10, user_id=None):
        request = post_pb2.ListPostsRequest(
            page=page,
            page_size=page_size
        )
        
        if user_id is not None:
            request.user_id = user_id
        
        try:
            response = self.stub.ListPosts(request)
            
            posts = [self.post_proto_to_dict(post) for post in response.posts]
            
            return {
                "posts": posts,
                "total_count": response.total_count,
                "page": response.page,
                "page_size": response.page_size,
                "total_pages": response.total_pages
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            raise Exception(f"gRPC error: {status_code}, {details}")
    
    def view_post(self, post_id, user_id):
        request = post_pb2.ViewPostRequest(
            post_id=post_id,
            user_id=user_id
        )
        
        try:
            response = self.stub.ViewPost(request)
            return {
                "success": response.success,
                "views_count": response.views_count
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            elif status_code == grpc.StatusCode.PERMISSION_DENIED:
                raise Exception(f"Permission denied: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
    
    def like_post(self, post_id, user_id, is_like=True):
        request = post_pb2.LikePostRequest(
            post_id=post_id,
            user_id=user_id,
            is_like=is_like
        )
        
        try:
            response = self.stub.LikePost(request)
            return {
                "success": response.success,
                "likes_count": response.likes_count,
                "is_liked": response.is_liked
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            elif status_code == grpc.StatusCode.PERMISSION_DENIED:
                raise Exception(f"Permission denied: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
    
    def comment_post(self, post_id, user_id, content):
        request = post_pb2.CommentPostRequest(
            post_id=post_id,
            user_id=user_id,
            content=content
        )
        
        try:
            response = self.stub.CommentPost(request)
            return self.comment_proto_to_dict(response)
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            elif status_code == grpc.StatusCode.PERMISSION_DENIED:
                raise Exception(f"Permission denied: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
    
    def list_comments(self, post_id, page=1, page_size=10):
        request = post_pb2.ListCommentsRequest(
            post_id=post_id,
            page=page,
            page_size=page_size
        )
        
        try:
            response = self.stub.ListComments(request)
            
            comments = [self.comment_proto_to_dict(comment) for comment in response.comments]
            
            return {
                "comments": comments,
                "total_count": response.total_count,
                "page": response.page,
                "page_size": response.page_size,
                "total_pages": response.total_pages
            }
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            if status_code == grpc.StatusCode.NOT_FOUND:
                raise Exception(f"Post not found: {details}")
            else:
                raise Exception(f"gRPC error: {status_code}, {details}")
