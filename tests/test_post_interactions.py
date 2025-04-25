import unittest
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class TestPostInteractions(unittest.TestCase):
    def setUp(self):
        # Register a test user
        self.user_data = {
            "login": f"testuser_{int(time.time())}",
            "password": "Password123",
            "email": f"test_{int(time.time())}@example.com",
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "1990-01-01",
            "phone": "+12345678901"
        }
        
        # Register the user
        register_response = requests.post(
            f"{BASE_URL}/register",
            json=self.user_data
        )
        self.assertEqual(register_response.status_code, 200)
        self.user = register_response.json()
        
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={
                "login": self.user_data["login"],
                "password": self.user_data["password"]
            }
        )
        self.assertEqual(login_response.status_code, 200)
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a test post
        self.post_data = {
            "title": f"Test Post {int(time.time())}",
            "description": "This is a test post for interaction testing",
            "is_private": False,
            "tags": ["test", "interaction"]
        }
        
        post_response = requests.post(
            f"{BASE_URL}/posts",
            headers=self.headers,
            json=self.post_data
        )
        self.assertEqual(post_response.status_code, 201)
        self.post = post_response.json()
    
    def test_view_post(self):
        """Test viewing a post"""
        # View the post
        view_response = requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/view",
            headers=self.headers
        )
        
        self.assertEqual(view_response.status_code, 200)
        view_data = view_response.json()
        
        # Check response structure
        self.assertIn("success", view_data)
        self.assertIn("views_count", view_data)
        self.assertTrue(view_data["success"])
        self.assertGreaterEqual(view_data["views_count"], 1)
        
        # View again - should not increase count for same user
        view_response2 = requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/view",
            headers=self.headers
        )
        
        self.assertEqual(view_response2.status_code, 200)
        view_data2 = view_response2.json()
        
        # Count should be the same
        self.assertEqual(view_data["views_count"], view_data2["views_count"])
    
    def test_like_post(self):
        """Test liking and unliking a post"""
        # Like the post
        like_response = requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/like",
            headers=self.headers,
            json={"is_like": True}
        )
        
        self.assertEqual(like_response.status_code, 200)
        like_data = like_response.json()
        
        # Check response structure
        self.assertIn("success", like_data)
        self.assertIn("likes_count", like_data)
        self.assertIn("is_liked", like_data)
        self.assertTrue(like_data["success"])
        self.assertEqual(like_data["likes_count"], 1)
        self.assertTrue(like_data["is_liked"])
        
        # Unlike the post
        unlike_response = requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/like",
            headers=self.headers,
            json={"is_like": False}
        )
        
        self.assertEqual(unlike_response.status_code, 200)
        unlike_data = unlike_response.json()
        
        # Check response structure
        self.assertTrue(unlike_data["success"])
        self.assertEqual(unlike_data["likes_count"], 0)
        self.assertFalse(unlike_data["is_liked"])
    
    def test_comment_post(self):
        """Test commenting on a post"""
        # Add a comment
        comment_data = {
            "content": f"Test comment {int(time.time())}"
        }
        
        comment_response = requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/comments",
            headers=self.headers,
            json=comment_data
        )
        
        self.assertEqual(comment_response.status_code, 200)
        comment = comment_response.json()
        
        # Check response structure
        self.assertIn("id", comment)
        self.assertIn("post_id", comment)
        self.assertIn("user_id", comment)
        self.assertIn("content", comment)
        self.assertIn("created_at", comment)
        
        self.assertEqual(comment["post_id"], self.post["id"])
        self.assertEqual(comment["user_id"], self.user["id"])
        self.assertEqual(comment["content"], comment_data["content"])
    
    def test_list_comments(self):
        """Test listing comments for a post"""
        # Add a few comments
        for i in range(3):
            comment_data = {
                "content": f"Test comment {i} - {int(time.time())}"
            }
            
            comment_response = requests.post(
                f"{BASE_URL}/posts/{self.post['id']}/comments",
                headers=self.headers,
                json=comment_data
            )
            
            self.assertEqual(comment_response.status_code, 200)
        
        # Get comments
        comments_response = requests.get(
            f"{BASE_URL}/posts/{self.post['id']}/comments",
            headers=self.headers
        )
        
        self.assertEqual(comments_response.status_code, 200)
        comments_data = comments_response.json()
        
        # Check response structure
        self.assertIn("comments", comments_data)
        self.assertIn("total_count", comments_data)
        self.assertIn("page", comments_data)
        self.assertIn("page_size", comments_data)
        self.assertIn("total_pages", comments_data)
        
        # Should have at least 3 comments
        self.assertGreaterEqual(len(comments_data["comments"]), 3)
        self.assertGreaterEqual(comments_data["total_count"], 3)
        
        # Check comment structure
        comment = comments_data["comments"][0]
        self.assertIn("id", comment)
        self.assertIn("post_id", comment)
        self.assertIn("user_id", comment)
        self.assertIn("content", comment)
        self.assertIn("created_at", comment)
    
    def test_get_post_with_counts(self):
        """Test that post retrieval includes view, like, and comment counts"""
        # Add a view
        requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/view",
            headers=self.headers
        )
        
        # Add a like
        requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/like",
            headers=self.headers,
            json={"is_like": True}
        )
        
        # Add a comment
        requests.post(
            f"{BASE_URL}/posts/{self.post['id']}/comments",
            headers=self.headers,
            json={"content": "Test comment"}
        )
        
        # Get the post
        post_response = requests.get(
            f"{BASE_URL}/posts/{self.post['id']}",
            headers=self.headers
        )
        
        self.assertEqual(post_response.status_code, 200)
        post_data = post_response.json()
        
        # Check counts
        self.assertIn("views_count", post_data)
        self.assertIn("likes_count", post_data)
        self.assertIn("comments_count", post_data)
        
        self.assertGreaterEqual(post_data["views_count"], 1)
        self.assertGreaterEqual(post_data["likes_count"], 1)
        self.assertGreaterEqual(post_data["comments_count"], 1)

if __name__ == "__main__":
    unittest.main()
