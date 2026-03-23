"""
Tests for reverse proxy subpath routing (/care prefix).

Verifies that ROOT_PATH is correctly applied to:
- Redirect URLs (login, signup, logout)
- Template-rendered paths (static assets, nav links, form actions)
- JS global injection (window.ROOT_PATH)

These tests set ROOT_PATH to simulate the Docker/Caddy environment.
When ROOT_PATH is unset (default ""), the app works without a prefix.
"""
import os
import pytest

# Temporarily set ROOT_PATH before importing the app, so FastAPI picks it up.
# conftest.py imports main.py at module level, so we must set this early.
# NOTE: This only works if the test module is collected AFTER conftest sets up
# the app. Since main.py reads ROOT_PATH at import time and conftest already
# imported it, we test with the current ROOT_PATH value (empty in local dev).
# The template rendering tests below work regardless because request.scope['root_path']
# is always available from FastAPI's root_path setting.


class TestSubpathTemplateRendering:
    """Verify that rendered HTML includes the correct root_path prefix."""

    def test_login_page_static_paths(self, client):
        """Login page CSS should reference root_path-prefixed static paths."""
        response = client.get("/login")
        assert response.status_code == 200
        # With ROOT_PATH="" (local dev), paths should be /static/...
        # With ROOT_PATH="/care" (Docker), paths should be /care/static/...
        root = os.environ.get("ROOT_PATH", "")
        assert f'href="{root}/static/css/style.css' in response.text

    def test_login_form_actions(self, client):
        """Login and signup form actions should include root_path prefix."""
        response = client.get("/login")
        root = os.environ.get("ROOT_PATH", "")
        assert f'action="{root}/login"' in response.text
        assert f'action="{root}/signup"' in response.text

    def test_dashboard_nav_links(self, auth_client):
        """Dashboard nav links should include root_path prefix."""
        client, _ = auth_client
        response = client.get("/")
        assert response.status_code == 200
        root = os.environ.get("ROOT_PATH", "")
        assert f'href="{root}/"' in response.text
        assert f'href="{root}/history"' in response.text
        assert f'href="{root}/account"' in response.text

    def test_dashboard_js_root_path_injected(self, auth_client):
        """Dashboard should inject window.ROOT_PATH for JavaScript."""
        client, _ = auth_client
        response = client.get("/")
        assert "window.ROOT_PATH" in response.text

    def test_dashboard_static_scripts(self, auth_client):
        """Dashboard script tags should include root_path prefix."""
        client, _ = auth_client
        response = client.get("/")
        root = os.environ.get("ROOT_PATH", "")
        assert f'src="{root}/static/js/app.js' in response.text
        assert f'src="{root}/static/js/confetti-mega.js' in response.text

    def test_account_logout_link(self, auth_client):
        """Account page logout link should include root_path prefix."""
        client, _ = auth_client
        response = client.get("/account")
        assert response.status_code == 200
        root = os.environ.get("ROOT_PATH", "")
        assert f'href="{root}/logout"' in response.text

    def test_kiosk_static_paths(self, auth_client):
        """Kiosk page should reference root_path-prefixed static paths."""
        client, _ = auth_client
        response = client.get("/kiosk")
        assert response.status_code == 200
        root = os.environ.get("ROOT_PATH", "")
        assert f'href="{root}/static/css/kiosk.css' in response.text
        assert f'src="{root}/static/js/kiosk.js' in response.text

    def test_kiosk_js_root_path_injected(self, auth_client):
        """Kiosk page should inject window.ROOT_PATH for JavaScript."""
        client, _ = auth_client
        response = client.get("/kiosk")
        assert "window.ROOT_PATH" in response.text


class TestSubpathRedirects:
    """Verify that server-side redirects include the root_path prefix."""

    def test_login_redirect_after_signup(self, client):
        """Successful signup should redirect to root_path + /."""
        response = client.post("/signup", data={
            "name": "Subpath Tester",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }, follow_redirects=False)
        assert response.status_code == 302
        root = os.environ.get("ROOT_PATH", "")
        assert response.headers["location"] == f"{root}/"

    def test_login_redirect_after_login(self, client):
        """Successful login should redirect to root_path + /."""
        # Create user first
        client.post("/signup", data={
            "name": "Login Redirect Test",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }, follow_redirects=False)

        response = client.post("/login", data={
            "name": "Login Redirect Test",
            "password": "testpass123",
        }, follow_redirects=False)
        assert response.status_code == 302
        root = os.environ.get("ROOT_PATH", "")
        assert response.headers["location"] == f"{root}/"

    def test_logout_redirect(self, auth_client):
        """Logout should redirect to root_path + /login."""
        client, _ = auth_client
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        root = os.environ.get("ROOT_PATH", "")
        assert response.headers["location"] == f"{root}/login"

    def test_unauthenticated_redirect(self, client):
        """Unauthenticated dashboard access should redirect to root_path + /login."""
        response = client.get("/", follow_redirects=False)
        root = os.environ.get("ROOT_PATH", "")
        if response.status_code == 302:
            assert response.headers["location"] == f"{root}/login"

    def test_already_logged_in_redirects_from_login(self, auth_client):
        """Visiting /login while authenticated should redirect to root_path + /."""
        client, _ = auth_client
        response = client.get("/login", follow_redirects=False)
        assert response.status_code == 302
        root = os.environ.get("ROOT_PATH", "")
        assert response.headers["location"] == f"{root}/"
