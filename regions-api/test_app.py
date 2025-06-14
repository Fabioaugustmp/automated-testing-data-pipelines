import os
import json
import pytest
from app import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Cria um db.json fake para os testes
    db_path = tmp_path / "db.json"
    db_content = {
        "mcc": [{"id": 1, "name": "Loja"}],
        "categories": [{"id": 1, "name": "Varejo"}]
    }
    db_path.write_text(json.dumps(db_content))
    monkeypatch.setenv("PORT", "5001")
    # Monkeypatch open para usar o db.json fake
    orig_open = open
    def fake_open(file, mode='r', *args, **kwargs):
        if file == "db.json":
            return orig_open(db_path, mode, *args, **kwargs)
        return orig_open(file, mode, *args, **kwargs)
    monkeypatch.setattr("builtins.open", fake_open)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_resource(client):
    resp = client.get("/mcc")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_get_resource_by_id(client):
    resp = client.get("/mcc/1")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == 1

def test_get_resource_not_found(client):
    resp = client.get("/foo")
    assert resp.status_code == 404

def test_post_resource(client):
    resp = client.post("/mcc", json={"id": 2, "name": "Padaria"})
    assert resp.status_code == 201
    assert any(item["id"] == 2 for item in resp.get_json())

def test_put_resource(client):
    resp = client.put("/mcc/1", json={"id": 1, "name": "Loja Atualizada"})
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Loja Atualizada"

def test_patch_resource(client):
    resp = client.patch("/mcc/1", json={"name": "Loja Patch"})
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Loja Patch"

def test_delete_resource(client):
    resp = client.delete("/mcc/1")
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "mcc deleted"

