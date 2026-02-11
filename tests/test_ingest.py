"""
Integration tests for submission and task endpoints.

These tests verify the ingest API endpoints work correctly
with actual database operations.
"""

import pytest
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestSubmitEndpoint:
    """Tests for POST /submit endpoint."""
    
    def test_submit_book_success(self, client):
        """Test successful book submission."""
        payload = {
            "title": "Designing Data-Intensive Applications",
            "author_name": "Martin Kleppmann",
            "amazon_url": "https://www.amazon.com/Designing-Data-Intensive-Applications-1491901632/",
            "goodreads_url": "https://www.goodreads.com/book/show/23463279",
            "author_site": "https://www.linkedin.com/in/martinkleppmann/",
            "other_links": [],
        }
        
        response = client.post("/submit", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["title"] == payload["title"]
        assert data["author_name"] == payload["author_name"]
        assert data["amazon_url"] == payload["amazon_url"]
        assert data["status"] == "pending_scrape"
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_submit_book_minimal(self, client):
        """Test submission with minimal required fields."""
        payload = {
            "title": "Clean Code",
            "author_name": "Robert Martin",
            "amazon_url": "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/",
        }
        
        response = client.post("/submit", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["goodreads_url"] is None
        assert data["author_site"] is None
    
    def test_submit_book_invalid_url(self, client):
        """Test submission with invalid URL."""
        payload = {
            "title": "Test Book",
            "author_name": "Test Author",
            "amazon_url": "not-a-valid-url",
        }
        
        response = client.post("/submit", json=payload)
        
        # Pydantic validation should reject invalid URL
        assert response.status_code == 422
    
    def test_submit_book_missing_required_field(self, client):
        """Test submission with missing required field."""
        payload = {
            "title": "Test Book",
            # Missing author_name
            "amazon_url": "https://www.amazon.com/test/",
        }
        
        response = client.post("/submit", json=payload)
        
        assert response.status_code == 422

    def test_submit_book_empty_optional_urls(self, client):
        """Test submission with empty optional URL fields from form inputs."""
        payload = {
            "title": "The Pragmatic Programmer",
            "author_name": "Andrew Hunt",
            "amazon_url": "https://www.amazon.com/pragmatic-programmer/",
            "goodreads_url": "",
            "author_site": "",
        }

        response = client.post("/submit", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["goodreads_url"] is None
        assert data["author_site"] is None
    
    def test_submit_health(self, client):
        """Test submit endpoint health check."""
        response = client.get("/submit/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["endpoint"] == "submit"


class TestTasksEndpoint:
    """Tests for /tasks endpoints."""
    
    def test_list_tasks_empty(self, client):
        """Test listing tasks when none exist."""
        response = client.get("/tasks")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "tasks" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "count" in data
        assert isinstance(data["tasks"], list)
    
    def test_list_tasks_with_pagination(self, client):
        """Test listing tasks with skip/limit."""
        # Create some test submissions first
        for i in range(3):
            payload = {
                "title": f"Book {i}",
                "author_name": f"Author {i}",
                "amazon_url": f"https://www.amazon.com/test{i}/",
            }
            client.post("/submit", json=payload)
        
        # List with pagination
        response = client.get("/tasks?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) <= 2
        assert data["skip"] == 0
        assert data["limit"] == 2
    
    def test_list_tasks_invalid_limit(self, client):
        """Test listing with invalid limit (>100)."""
        response = client.get("/tasks?limit=150")
        
        # Should be rejected by validation
        assert response.status_code == 422
    
    def test_get_task_success(self, client):
        """Test getting task details."""
        # Create a submission first
        payload = {
            "title": "Test Book",
            "author_name": "Test Author",
            "amazon_url": "https://www.amazon.com/test-unique/",
        }
        create_response = client.post("/submit", json=payload)
        submission_id = create_response.json()["id"]
        
        # Get task details
        response = client.get(f"/tasks/{submission_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "submission" in data
        assert "book" in data
        assert "progress" in data
        
        # Verify submission data
        assert data["submission"]["id"] == submission_id
        assert data["submission"]["title"] == "Test Book"
        
        # Verify progress tracking
        assert "current_stage" in data["progress"]
        assert "steps" in data["progress"]
        assert len(data["progress"]["steps"]) == 4
    
    def test_get_task_not_found(self, client):
        """Test getting non-existent task."""
        response = client.get("/tasks/507f1f77bcf86cd799439011")
        
        # Should return 404 for valid ObjectId that doesn't exist
        # Note: 507f1f77bcf86cd799439011 is valid MongoDB ObjectId format
        # but doesn't exist, so might return 404
        assert response.status_code in [404, 422]
    
    def test_get_task_invalid_id(self, client):
        """Test getting task with invalid ID format."""
        response = client.get("/tasks/not-a-valid-id")
        
        # Should handle invalid ObjectId gracefully
        assert response.status_code in [404, 422]
    
    def test_tasks_health(self, client):
        """Test tasks endpoint health check."""
        response = client.get("/tasks/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["endpoint"] == "tasks"
