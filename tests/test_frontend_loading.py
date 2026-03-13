import pytest

class TestFrontend:
    def test_login_page_loads(self, client):
        """Test that the login page loads for unauthenticated users."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "Log In" in response.text
        assert "Sign Up" in response.text

    def test_dashboard_loads_when_authenticated(self, auth_client):
        """Test that the main dashboard page loads for authenticated users."""
        client, _ = auth_client
        response = client.get("/")
        assert response.status_code == 200
        assert "Care-Tracker" in response.text

    def test_history_page_loads_when_authenticated(self, auth_client):
        """Test that the history page loads for authenticated users."""
        client, _ = auth_client
        response = client.get("/history")
        assert response.status_code == 200
        assert "History" in response.text

    def test_dashboard_redirects_when_not_authenticated(self, client):
        """Unauthenticated access to dashboard should redirect to login."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (302, 401)
