from io import BytesIO

import pytest
import pytest_asyncio


class TestAPIEndpoints:
    """Test API endpoint functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test the root endpoint returns service info"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "Image Feature Detection API"
        assert data["status"] == "running"
        assert "/process-image" in data["endpoints"]
        assert "/check-status" in data["endpoints"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_status_endpoint(self, client):
        """Test the status endpoint returns readiness info"""
        response = await client.get("/check-status")

        assert response.status_code == 200
        data = response.json()

        # Check expected fields exist
        assert "service_ready" in data
        assert "detector_ready" in data
        assert "warmup_completed" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))

class TestAPIValidation:
    """Test API input validation and error handling"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_non_image_file_rejected(self, client):
        """Test that non-image files are rejected"""
        files = {"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
        response = await client.post("/process-image", files=files)

        assert response.status_code == 400
        response_data = response.json()
        assert "error" in response_data or "detail" in response_data
        error_msg = response_data.get("error", response_data.get("detail", ""))
        assert "File must be an image" in error_msg

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_file_rejected(self, client):
        """Test that empty files are rejected"""
        files = {"file": ("empty.jpg", BytesIO(b""), "image/jpeg")}
        response = await client.post("/process-image", files=files)

        # API might return 400 or 500 for empty files, both are acceptable error handling
        assert response.status_code in [400, 500]
        response_data = response.json()
        assert "error" in response_data or "detail" in response_data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_file_parameter(self, client):
        """Test that missing file parameter returns validation error"""
        response = await client.post("/process-image")

        assert response.status_code == 422  # Unprocessable Entity