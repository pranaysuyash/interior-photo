"""
Tests for transformation API endpoints

Tests cover:
- Creating transformations
- Retrieving transformation status
- Transformation history
- Credit usage
- Rate limiting
- File upload validation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.transformation import Transformation


class TestCreateTransformation:
    """Test transformation creation endpoint"""

    def test_create_transformation_authenticated(
        self, client: TestClient, auth_headers: dict, sample_image_file,
        mock_s3_service, mock_replicate_service, db: Session
    ):
        """Test creating transformation as authenticated user"""
        files = {"image": sample_image_file}
        data = {
            "vibe": "modern",
            "colors": "neutral",
            "description": "Beautiful living room"
        }

        response = client.post(
            "/api/v1/transform/transform",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert "job_id" in result
        assert "status" in result
        assert result["vibe"] == "modern"
        assert result["colors"] == "neutral"

    def test_create_transformation_insufficient_credits(
        self, client: TestClient, auth_headers: dict, sample_image_file,
        test_user: User, db: Session
    ):
        """Test transformation creation with insufficient credits"""
        # Set user credits to 0
        test_user.credits = 0
        db.commit()

        files = {"image": sample_image_file}
        data = {"vibe": "modern", "colors": "neutral"}

        response = client.post(
            "/api/v1/transform/transform",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 402
        assert "insufficient credits" in response.json()["detail"].lower()

    def test_create_transformation_invalid_vibe(
        self, client: TestClient, auth_headers: dict, sample_image_file
    ):
        """Test transformation with invalid vibe"""
        files = {"image": sample_image_file}
        data = {"vibe": "invalid_vibe", "colors": "neutral"}

        response = client.post(
            "/api/v1/transform/transform",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_transformation_missing_image(
        self, client: TestClient, auth_headers: dict
    ):
        """Test transformation without image upload"""
        data = {"vibe": "modern", "colors": "neutral"}

        response = client.post(
            "/api/v1/transform/transform",
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_transformation_with_references(
        self, client: TestClient, auth_headers: dict, sample_image_file,
        mock_s3_service, mock_replicate_service
    ):
        """Test transformation with reference images"""
        files = {
            "image": sample_image_file,
            "reference_images": [sample_image_file, sample_image_file]
        }
        data = {
            "vibe": "modern",
            "colors": "neutral",
            "description": "Add furniture from references"
        }

        response = client.post(
            "/api/v1/transform/transform",
            files=files,
            data=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert "job_id" in result


class TestGetTransformationStatus:
    """Test transformation status retrieval"""

    def test_get_transformation_status(
        self, client: TestClient, auth_headers: dict,
        sample_transformation: Transformation
    ):
        """Test retrieving transformation status"""
        response = client.get(
            f"/api/v1/transform/{sample_transformation.job_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == sample_transformation.job_id
        assert data["status"] == "COMPLETED"
        assert "transformed_image_url" in data

    def test_get_nonexistent_transformation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test retrieving nonexistent transformation"""
        response = client.get(
            "/api/v1/transform/nonexistent-job-id",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_transformation_unauthorized(
        self, client: TestClient, sample_transformation: Transformation
    ):
        """Test retrieving transformation without authentication"""
        response = client.get(
            f"/api/v1/transform/{sample_transformation.job_id}"
        )

        assert response.status_code == 401


class TestTransformationHistory:
    """Test transformation history endpoint"""

    def test_get_transformation_history(
        self, client: TestClient, auth_headers: dict,
        sample_transformation: Transformation
    ):
        """Test retrieving transformation history"""
        response = client.get(
            "/api/v1/transform/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "transformations" in data
        assert len(data["transformations"]) > 0
        assert data["transformations"][0]["job_id"] == sample_transformation.job_id

    def test_get_transformation_history_pagination(
        self, client: TestClient, auth_headers: dict
    ):
        """Test transformation history pagination"""
        response = client.get(
            "/api/v1/transform/history?limit=5&offset=0",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "transformations" in data
        assert "total" in data

    def test_get_transformation_history_empty(
        self, client: TestClient, pro_auth_headers: dict
    ):
        """Test transformation history for user with no transformations"""
        response = client.get(
            "/api/v1/transform/history",
            headers=pro_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["transformations"]) == 0
