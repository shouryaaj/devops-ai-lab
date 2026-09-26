import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, apply_discount, get_port  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_product_found(client):
    r = client.get("/products/1")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Notebook"


def test_product_missing_returns_404(client):
    r = client.get("/products/999")
    assert r.status_code == 404


def test_apply_discount():
    assert apply_discount(100, 10) == 90.0
    assert apply_discount(899, 0) == 899.0


def test_apply_discount_rejects_bad_percent():
    with pytest.raises(ValueError):
        apply_discount(100, 150)


def test_price_endpoint(client):
    r = client.get("/products/1/price?discount=20")
    assert r.status_code == 200
    assert r.get_json()["final_price"] == 40.0


def test_default_port(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    assert get_port() == 5000
