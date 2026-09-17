from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def test_create_work(client):

    response = client.post(
        "/works",
        json={
            "openalex_id": "W_API_TEST",
            "title": "API Test Article",
            "publication_year": 2026,
            "cited_by_count": 100,
            "doi": None,
        },
    )


    assert response.status_code == 201


    data = response.json()

    assert data["openalex_id"] == "W_API_TEST"
    assert data["title"] == "API Test Article"


def test_create_work_duplicate(client):

    payload = {
        "openalex_id": "W_API_DUPLICATE",
        "title": "Duplicate API Test",
        "publication_year": 2026,
        "cited_by_count": 10,
    }

    first = client.post(
        "/works",
        json=payload,
    )

    assert first.status_code == 201


    second = client.post(
        "/works",
        json=payload,
    )

    assert second.status_code == 409
    assert second.json()["detail"] == (
        "Work with this OpenAlex ID already exists"
    )


def test_get_work(client):

    response = client.post(
        "/works",
        json={
            "openalex_id": "W_API_GET",
            "title": "Get API Test",
            "publication_year": 2025,
            "cited_by_count": 50,
        },
    )

    work_id = response.json()["id"]


    response = client.get(
        f"/works/{work_id}"
    )


    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Get API Test"


def test_get_work_not_found(client):

    response = client.get(
        "/works/999999"
    )

    assert response.status_code == 404