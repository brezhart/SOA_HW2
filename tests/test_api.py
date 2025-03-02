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
    print("DBG GREP: ",  response.json())
    return response.json()["access_token"]


def test_register_user(test_user):
    response = requests.post(f"{BASE_URL}/register", json=test_user)
    assert response.status_code == 200
    assert response.json()["login"] == test_user["login"]

def test_login_success(registered_user):
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "login": registered_user["login"],
            "password": registered_user["password"]
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_get_profile(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/profile", headers=headers)
    assert response.status_code == 200
    assert "email" in response.json()

def test_update_profile(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    new_name = "Updated_" + fake.first_name()
    response = requests.put(
        f"{BASE_URL}/profile",
        json={"first_name": new_name},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == new_name

def test_invalid_login(registered_user):
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "login": registered_user["login"],
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401
