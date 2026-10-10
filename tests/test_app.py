import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Practice chess",
        "schedule": "Fridays",
        "max_participants": 2,
        "participants": ["alex@example.com"],
    },
    "Full Activity": {
        "description": "Already full",
        "schedule": "Mondays",
        "max_participants": 1,
        "participants": ["student@example.com"],
    },
}


@pytest.fixture
def client(monkeypatch):
    # Arrange: give each test fresh in-memory state.
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(TEST_ACTIVITIES))
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activity_data(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == TEST_ACTIVITIES


def test_signup_adds_participant(client):
    # Arrange
    email = "new.student@example.com"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    email = "new.student@example.com"

    # Act
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = "alex@example.com"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_rejects_full_activity(client):
    # Arrange
    email = "new.student@example.com"

    # Act
    response = client.post("/activities/Full%20Activity/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_unregister_removes_participant(client):
    # Arrange
    email = "alex@example.com"

    # Act
    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    email = "alex@example.com"

    # Act
    response = client.delete("/activities/Unknown%20Activity/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    email = "not.registered@example.com"

    # Act
    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }