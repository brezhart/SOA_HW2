import pytest
import time
from faker import Faker
import requests

BASE_URL = "http://localhost:8000"
fake = Faker()


@pytest.fixture(scope="function")
def test_user():
    return {
        "login": fake.user_name(),
        "password": "ValidPass123",
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name()
    }


@pytest.fixture(scope="function")
def registered_user(test_user):
    response = requests.post(f"{BASE_URL}/register", json=test_user)
    assert response.status_code == 200
    return test_user


@pytest.fixture(scope="function")
def auth_token(registered_user):
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "login": registered_user["login"],
            "password": registered_user["password"]
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def test_post():
    return {
        "title": fake.sentence(),
        "description": fake.paragraph(),
        "is_private": False,
        "tags": [fake.word(), fake.word()]
    }


@pytest.fixture(scope="function")
def created_post(auth_token, test_post):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{BASE_URL}/posts", json=test_post, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_create_post(auth_token, test_post):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{BASE_URL}/posts", json=test_post, headers=headers)
    assert response.status_code == 201
    assert response.json()["title"] == test_post["title"]
    assert response.json()["description"] == test_post["description"]
    assert response.json()["is_private"] == test_post["is_private"]
    assert set(response.json()["tags"]) == set(test_post["tags"])
    assert "id" in response.json()
    assert "creator_id" in response.json()
    assert "created_at" in response.json()
    assert "updated_at" in response.json()


def test_get_post(auth_token, created_post):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/posts/{created_post['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_post["id"]
    assert response.json()["title"] == created_post["title"]
    assert response.json()["description"] == created_post["description"]


def test_update_post(auth_token, created_post):
    headers = {"Authorization": f"Bearer {auth_token}"}
    update_data = {
        "title": "Updated Title",
        "description": "Updated description",
        "is_private": True,
        "tags": ["updated", "test"]
    }
    response = requests.put(
        f"{BASE_URL}/posts/{created_post['id']}",
        json=update_data,
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == created_post["id"]
    assert response.json()["title"] == update_data["title"]
    assert response.json()["description"] == update_data["description"]
    assert response.json()["is_private"] == update_data["is_private"]
    assert set(response.json()["tags"]) == set(update_data["tags"])


def test_list_posts(auth_token, created_post):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/posts", headers=headers)
    assert response.status_code == 200
    assert "posts" in response.json()
    assert "total_count" in response.json()
    assert "page" in response.json()
    assert "page_size" in response.json()
    assert "total_pages" in response.json()
    assert len(response.json()["posts"]) > 0
    
    # Test pagination
    response = requests.get(f"{BASE_URL}/posts?page=1&page_size=5", headers=headers)
    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 5


def test_delete_post(auth_token, created_post):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.delete(f"{BASE_URL}/posts/{created_post['id']}", headers=headers)
    assert response.status_code == 204
    
    # Verify post is deleted
    response = requests.get(f"{BASE_URL}/posts/{created_post['id']}", headers=headers)
    assert response.status_code == 404


def test_private_post_access(auth_token):
    # Create a private post
    headers = {"Authorization": f"Bearer {auth_token}"}
    private_post = {
        "title": "Private Post",
        "description": "This is a private post",
        "is_private": True,
        "tags": ["private", "test"]
    }
    response = requests.post(f"{BASE_URL}/posts", json=private_post, headers=headers)
    assert response.status_code == 201
    post_id = response.json()["id"]
    
    # Create another user
    second_user = {
        "login": fake.user_name(),
        "password": "ValidPass123",
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name()
    }
    response = requests.post(f"{BASE_URL}/register", json=second_user)
    assert response.status_code == 200
    
    # Login as second user
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "login": second_user["login"],
            "password": second_user["password"]
        }
    )
    assert response.status_code == 200
    second_token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {second_token}"}
    response = requests.get(f"{BASE_URL}/posts/{post_id}", headers=headers)
    assert response.status_code == 403  # Forbidden


def test_unauthorized_access():
    # Try to access posts without authentication
    response = requests.get(f"{BASE_URL}/posts")
    assert response.status_code == 401  # Unauthorized
    
    response = requests.post(f"{BASE_URL}/posts", json={"title": "Test", "description": "Test"})
    assert response.status_code == 401  # Unauthorized


def test_invalid_post_data(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    invalid_post = {
        "title": "Test"
        # Missing description
    }
    response = requests.post(f"{BASE_URL}/posts", json=invalid_post, headers=headers)
    assert response.status_code in [422]
    
    invalid_post = {
        "title": "",
        "description": "Test description"
    }
    response = requests.post(f"{BASE_URL}/posts", json=invalid_post, headers=headers)
    assert response.status_code in [422]
