import pytest

class TestFrontend:
    def test_dashboard_loads(self, client):
        """Test that the main dashboard page loads."""
        response = client.get("/")
        assert response.status_code == 200
        # Check for some expected HTML content
        assert "Care-Tracker" in response.text

    def test_history_page_loads(self, client):
        """Test that the history page loads."""
        response = client.get("/history")
        assert response.status_code == 200
        assert "History" in response.text

