"""API-тесты без сети: TestClient."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.ledger import get_ledger


@pytest.fixture()
def client() -> TestClient:
    get_ledger().clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_ledger().clear()


def _seed(client: TestClient) -> None:
    client.post(
        "/api/v1/transactions",
        json={"kind": "income", "amount": 100000, "category": "salary", "date": "2026-09-01"},
    )
    client.post(
        "/api/v1/transactions",
        json={"kind": "expense", "amount": 20000, "category": "food", "date": "2026-09-05"},
    )
    client.post("/api/v1/budgets", json={"category": "food", "monthly_limit": 15000})


def test_health(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_summary_flow(client: TestClient) -> None:
    _seed(client)
    resp = client.get("/api/v1/summary?month=2026-09")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["savings"] == 80000.0
    assert payload["savings_rate"] == 0.8


def test_alerts_flow(client: TestClient) -> None:
    _seed(client)
    resp = client.get("/api/v1/alerts?month=2026-09")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["over_by"] == 5000.0


def test_rejects_bad_date(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/transactions",
        json={"kind": "expense", "amount": 10, "category": "food", "date": "2026-13-40"},
    )
    assert resp.status_code == 422


@pytest.mark.integration()
def test_budgets_shape(client: TestClient) -> None:
    """Интеграционный по маркеру: бюджеты, без сети."""
    _seed(client)
    resp = client.get("/api/v1/budgets")
    assert resp.status_code == 200
    assert resp.json() == [{"category": "food", "monthly_limit": 15000.0}]
