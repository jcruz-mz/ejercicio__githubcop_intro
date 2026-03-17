import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Keep a pristine copy of the initial activity state so we can reset between tests.
_initial_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(_initial_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(_initial_activities))


client = TestClient(app)


def test_get_activities_returns_expected_map():
    # Arrange
    expected = copy.deepcopy(_initial_activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_adds_participant_and_idempotency_is_handled():
    # Arrange
    activity_name = "Chess Club"
    email = "teststudent@mergington.edu"

    # Act: sign up
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]

    # Act: sign up again should fail
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400


def test_signup_unknown_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "teststudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404


def test_unregister_removes_participant_and_idempotency_is_handled():
    # Arrange
    activity_name = "Chess Club"
    existing_email = _initial_activities[activity_name]["participants"][0]

    # Act: unregister
    response = client.post(f"/activities/{activity_name}/unregister", params={"email": existing_email})

    # Assert
    assert response.status_code == 200
    assert existing_email not in activities[activity_name]["participants"]

    # Act: unregister again should fail
    response = client.post(f"/activities/{activity_name}/unregister", params={"email": existing_email})

    # Assert
    assert response.status_code == 400


def test_unregister_unknown_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "teststudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/unregister", params={"email": email})

    # Assert
    assert response.status_code == 404


def test_root_redirects_to_static_index():
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (307, 308)
    assert response.headers["location"].endswith("/static/index.html")
