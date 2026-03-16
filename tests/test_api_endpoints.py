import pytest
from datetime import date

class TestAPI:
    def test_info_endpoint_is_public(self, client):
        """GET /api/info should remain accessible without auth."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "care_day" in data

    def test_protected_endpoints_require_auth(self, client):
        """All data-bearing API endpoints should return 401 without a session cookie."""
        protected = [
            ("GET", "/api/pets"),
            ("GET", "/api/care-items"),
            ("GET", "/api/status"),
            ("GET", "/api/history"),
            ("GET", "/api/history/grid"),
            ("GET", "/api/users/search"),
        ]
        for method, path in protected:
            resp = client.request(method, path)
            assert resp.status_code == 401, f"{method} {path} should be 401, got {resp.status_code}"

    def test_create_and_get_pet(self, auth_client):
        """Test creating a pet and retrieving it."""
        client, _ = auth_client
        # Create
        response = client.post("/api/pets", json={
            "name": "TestDog",
            "species": "Dog",
            "notes": "Good boy"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestDog"
        pet_id = data["id"]

        # Get List
        response = client.get("/api/pets")
        assert response.status_code == 200
        pets = response.json()
        assert len(pets) >= 1
        assert any(p["id"] == pet_id for p in pets)

    def test_care_item_lifecycle(self, auth_client):
        """Test creating a care item, completing it, and undoing it."""
        client, _ = auth_client
        # 1. Create Pet
        pet_resp = client.post("/api/pets", json={"name": "Cat", "species": "Cat"})
        pet_id = pet_resp.json()["id"]

        # 2. Create Care Item
        item_resp = client.post("/api/care-items", json={
            "pet_id": pet_id,
            "name": "Meds",
            "category": "medication",
            "display_order": 1
        })
        assert item_resp.status_code == 200
        item_id = item_resp.json()["id"]

        # 3. Verify it appears in status
        status_resp = client.get("/api/status")
        status_data = status_resp.json()
        
        # Find our pet in the list. The structure is {"pets": [{"pet": {...}, "tasks": [...]}]}
        pet_entry = next((p for p in status_data["pets"] if p["pet"]["id"] == pet_id), None)
        assert pet_entry is not None
        
        # Find our item in the tasks list
        # Task structure: {"care_item": {...}, "is_completed": bool}
        task_entry = next((t for t in pet_entry["tasks"] if t["care_item"]["id"] == item_id), None)
        assert task_entry is not None
        assert task_entry["is_completed"] == False

        # 4. Mark Complete
        complete_resp = client.post(f"/api/tasks/{item_id}/complete", json={"completed_by": "Tester"})
        assert complete_resp.status_code == 200
        
        # Verify status is now true
        status_resp = client.get("/api/status")
        pet_entry = next(p for p in status_resp.json()["pets"] if p["pet"]["id"] == pet_id)
        task_entry = next(t for t in pet_entry["tasks"] if t["care_item"]["id"] == item_id)
        assert task_entry["is_completed"] == True

        # 5. Undo
        undo_resp = client.post(f"/api/tasks/{item_id}/undo")
        assert undo_resp.status_code == 200

        # Verify status is back to false
        status_resp = client.get("/api/status")
        pet_entry = next(p for p in status_resp.json()["pets"] if p["pet"]["id"] == pet_id)
        task_entry = next(t for t in pet_entry["tasks"] if t["care_item"]["id"] == item_id)
        assert task_entry["is_completed"] == False
