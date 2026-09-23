from copy import deepcopy
from pathlib import Path
from urllib.parse import quote
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import app as app_module


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Reset the in-memory activity data before each test."""
    original_state = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_state)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert "participants" in payload[expected_activity]


def test_signup_for_activity_success(client):
    # Arrange
    activity = "Chess Club"
    email = "student@example.com"
    app_module.activities[activity]["participants"] = []

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_for_unknown_activity_returns_404(client):
    # Arrange
    activity = "Unknown Activity"
    email = "student@example.com"

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_duplicate_student_returns_400(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    app_module.activities[activity]["participants"] = [email]

    # Act
    response = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_unregister_participant_success(client):
    # Arrange
    activity = "Chess Club"
    email = "student@example.com"
    app_module.activities[activity]["participants"] = [email]

    # Act
    response = client.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_missing_participant_returns_404(client):
    # Arrange
    activity = "Chess Club"
    email = "missing@example.com"
    app_module.activities[activity]["participants"] = []

    # Act
    response = client.delete(f"/activities/{quote(activity)}/participants/{quote(email)}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found in this activity"}
