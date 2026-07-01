from app.auth.security import hash_password
from app.db.models import User, UserRole


def test_login_and_me(client, db):
    user = User(
        email="admin@test.com",
        name="Test Admin",
        role=UserRole.admin,
        password_hash=hash_password("secret123"),
        is_active=True,
    )
    db.add(user)
    db.commit()

    bad = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "wrong"})
    assert bad.status_code == 401

    res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@test.com"
    assert me.json()["role"] == "admin"


def test_admin_create_candidate(client, db):
    admin = User(
        email="admin@test.com",
        name="Admin",
        role=UserRole.admin,
        password_hash=hash_password("secret123"),
        is_active=True,
    )
    db.add(admin)
    db.commit()

    login = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/candidates",
        json={"first_name": "Raj", "last_name": "Kumar", "primary_skill": "DevOps"},
        headers=headers,
    )
    assert created.status_code == 200
    body = created.json()
    assert body["first_name"] == "Raj"
    assert body["resume_count"] == 0

    listed = client.get("/api/candidates", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
