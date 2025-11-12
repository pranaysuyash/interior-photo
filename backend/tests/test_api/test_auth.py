"""
Tests for authentication API endpoints

Tests cover:
- User registration
- User login
- Token validation
- Password validation
- Duplicate email handling
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestUserRegistration:
    """Test user registration endpoint"""

    def test_register_new_user(self, client: TestClient, db: Session):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "strongpassword123",
                "name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "name": "Duplicate User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "name": "Test User"
            }
        )
        assert response.status_code == 422

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "123",
                "name": "Test User"
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing fields"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422


class TestTokenValidation:
    """Test token validation and protected endpoints"""

    def test_access_protected_endpoint_with_valid_token(
        self, client: TestClient, auth_headers: dict
    ):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/api/v1/user/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/user/me")
        assert response.status_code == 401

    def test_access_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/v1/user/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
