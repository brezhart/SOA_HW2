import grpc
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp

import post_pb2
import post_pb2_grpc

# gRPC client for post service
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
            "tags": list(post_proto.tags)
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
