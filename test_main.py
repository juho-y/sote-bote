from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import SummaryFailure, SummaryResponse, app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.mark.anyio
async def test_summarize_endpoint_success(client):
    """Test the /summarize endpoint with a successful response."""
    mock_result = AsyncMock()
    mock_result.output = SummaryResponse(
        summary="Patient has persistent headache for 3 days.",
        key_points=["Persistent headache", "No fever", "Rest recommended"],
        language="en",
    )

    with patch("main.summarize_agent.run", return_value=mock_result):
        response = client.post(
            "/summarize",
            json={
                "text": "Patient reports persistent headache for 3 days. No fever.",
                "language": "en",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Patient has persistent headache for 3 days."
    assert len(data["key_points"]) == 3
    assert data["language"] == "en"


@pytest.mark.anyio
async def test_summarize_endpoint_failure(client):
    """Test the /summarize endpoint when agent returns failure."""
    mock_result = AsyncMock()
    mock_result.output = SummaryFailure(reason="Not a medical transcript")

    with patch("main.summarize_agent.run", return_value=mock_result):
        response = client.post(
            "/summarize",
            json={
                "text": "The quick brown fox jumps over the lazy dog.",
                "language": "en",
            },
        )

    assert response.status_code == 400
    assert "Not a medical transcript" in response.json()["detail"]


@pytest.mark.anyio
async def test_summarize_endpoint_finnish(client):
    """Test the /summarize endpoint with Finnish language."""
    mock_result = AsyncMock()
    mock_result.output = SummaryResponse(
        summary="Potilaalla on jatkuva päänsärky.",
        key_points=["Päänsärky 3 päivää", "Ei kuumetta"],
        language="fi",
    )

    with patch("main.summarize_agent.run", return_value=mock_result):
        response = client.post(
            "/summarize",
            json={
                "text": "Potilas valittaa päänsärkyä.",
                "language": "fi",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "päänsärky" in data["summary"].lower()
    assert data["language"] == "fi"


def test_get_summary_endpoint(client):
    """Test the /summary GET endpoint."""
    response = client.get("/summary")

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "key_points" in data
    assert "language" in data


def test_root_endpoint(client):
    """Test the root endpoint returns HTML."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
