import pytest

class TestUserIdentity:
    def test_user_signup_and_login(self, client):
        """Test that a user can sign up with password confirmation, then log in."""
        # Signup (password typed twice)
        response = client.post("/signup", data={
            "name": "Alice Wonderland",
            "password": "securepass1",
            "password_confirm": "securepass1",
        }, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/"

        # Login with the same credentials
        response = client.post("/login", data={
            "name": "Alice Wonderland",
            "password": "securepass1",
        }, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_signup_password_mismatch(self, client):
        """Signup should fail when passwords don't match."""
        response = client.post("/signup", data={
            "name": "Mismatch User",
            "password": "abc123",
            "password_confirm": "xyz789",
        })
        assert response.status_code == 200
        assert "do not match" in response.text

    def test_signup_short_password(self, client):
        """Signup should fail when password is shorter than 8 chars (SEC-11)."""
        response = client.post("/signup", data={
            "name": "Short Pass",
            "password": "abc1234",
            "password_confirm": "abc1234",
        })
        assert response.status_code == 200
        assert "at least" in response.text

    def test_login_wrong_password(self, client):
        """Login should fail with wrong password."""
        # First create a user
        client.post("/signup", data={
            "name": "Wrong Pass User",
            "password": "correct_pw",
            "password_confirm": "correct_pw",
        }, follow_redirects=False)

        # Try logging in with wrong password
        response = client.post("/login", data={
            "name": "Wrong Pass User",
            "password": "wrong_pw",
        })
        assert response.status_code == 200
        assert "Invalid" in response.text

    def test_user_search(self, auth_client):
        """Test searching for users."""
        client, user = auth_client
        # The auth_client fixture already created "Test User"
        # Create more users via check-in (legacy endpoint)
        client.post("/api/users/check-in", json={"name": "Bob Smith"})
        client.post("/api/users/check-in", json={"name": "Bobby Brown"})
        client.post("/api/users/check-in", json={"name": "Charlie"})

        response = client.get("/api/users/search?q=Bob")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        names = [u["name"] for u in data]
        assert "Bob Smith" in names
        assert "Bobby Brown" in names
        assert "Charlie" not in names

    def test_auto_registration_on_complete(self, auth_client):
        """Test that a user is registered when they complete a task."""
        client, _ = auth_client

        # Setup pet and care item
        pet_resp = client.post("/api/pets", json={"name": "TestPet", "species": "Dog"})
        pet_id = pet_resp.json()["id"]
        item_resp = client.post("/api/care-items", json={
            "pet_id": pet_id,
            "name": "TestTask",
            "category": "other"
        })
        item_id = item_resp.json()["id"]

        # Complete task as a new user name
        new_user_name = "Dave Discovery"
        response = client.post(f"/api/tasks/{item_id}/complete?completed_by={new_user_name}")
        assert response.status_code == 200

        # Verify user was auto-created in the registry
        search_resp = client.get(f"/api/users/search?q={new_user_name}")
        assert search_resp.status_code == 200
        users = search_resp.json()
        assert any(u["name"] == new_user_name for u in users)

    def test_change_password(self, auth_client):
        """Test that an authenticated user can change their password."""
        client, _ = auth_client

        response = client.post("/api/users/change-password", json={
            "current_password": "testpass123",
            "new_password": "newpass456",
            "new_password_confirm": "newpass456",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_change_password_wrong_current(self, auth_client):
        """Changing password with wrong current password should fail."""
        client, _ = auth_client

        response = client.post("/api/users/change-password", json={
            "current_password": "wrong_password",
            "new_password": "newpass456",
            "new_password_confirm": "newpass456",
        })
        assert response.status_code == 400

    def test_protected_routes_redirect_when_not_authenticated(self, client):
        """Dashboard, history, account should redirect to login when not authenticated."""
        for path in ["/", "/history", "/account"]:
            response = client.get(path, follow_redirects=False)
            # The middleware intercepts 401 and returns a 302 redirect to /login
            assert response.status_code in (302, 401), f"Expected redirect for {path}"
