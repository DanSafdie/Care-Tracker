import pytest

class TestUserIdentity:
    def test_user_check_in(self, client):
        """Test that a user can check-in and be registered."""
        # Check-in
        response = client.post("/api/users/check-in", json={"name": "Alice Wonderland"})
        assert response.status_code == 200
        data = response.json()
        
        # Structure is {"user": UserResponse, "is_new": bool}
        assert "user" in data
        user = data["user"]
        assert user["name"] == "Alice Wonderland"
        assert "id" in user
        assert "created_at" in user
        assert "last_seen" in user
        assert data["is_new"] is True

    def test_user_search(self, client):
        """Test searching for users."""
        # Register a few users
        client.post("/api/users/check-in", json={"name": "Bob Smith"})
        client.post("/api/users/check-in", json={"name": "Bobby Brown"})
        client.post("/api/users/check-in", json={"name": "Charlie"})

        # Search for "Bob"
        response = client.get("/api/users/search?q=Bob")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        names = [u["name"] for u in data]
        assert "Bob Smith" in names
        assert "Bobby Brown" in names
        assert "Charlie" not in names

    def test_auto_registration_on_complete(self, client):
        """Test that a user is registered when they complete a task."""
        # 1. Setup Pet and Item
        pet_resp = client.post("/api/pets", json={"name": "TestPet", "species": "Dog"})
        pet_id = pet_resp.json()["id"]
        item_resp = client.post("/api/care-items", json={
            "pet_id": pet_id,
            "name": "TestTask",
            "category": "other"
        })
        item_id = item_resp.json()["id"]

        # 2. Complete task as a new user
        new_user_name = "Dave Discovery"
        response = client.post(f"/api/tasks/{item_id}/complete?completed_by={new_user_name}")
        assert response.status_code == 200

        # 3. Verify user was created in the registry
        search_resp = client.get(f"/api/users/search?q={new_user_name}")
        assert search_resp.status_code == 200
        users = search_resp.json()
        assert any(u["name"] == new_user_name for u in users)

