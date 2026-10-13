from crm.extensions import db
from crm.models import ActivityLog, Client, User, UserRole


def create_user(email, role=UserRole.USER):
    user = User(
        first_name=email.split("@")[0].title(),
        last_name="Example",
        email=email,
        role=role,
    )
    user.set_password("correct-horse-battery-staple")
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_api_requires_authentication(client):
    response = client.get("/api/v1/clients")

    assert response.status_code == 401
    assert response.json == {"error": "Authentication required."}


def test_api_login_establishes_session_and_logout_clears_it(app, client):
    with app.app_context():
        create_user("ada@example.com")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": " ADA@example.com ",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 200
    assert response.json["user"]["email"] == "ada@example.com"

    listing = client.get("/api/v1/clients")
    assert listing.status_code == 200
    assert listing.json == {"data": []}

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204
    assert client.get("/api/v1/clients").status_code == 401


def test_api_client_crud_and_activity_logging(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        user_id = user.id
    login_as(client, user_id)

    created = client.post(
        "/api/v1/clients",
        json={
            "name": "  Grace Hopper ",
            "company": "  Navy ",
            "email": " GRACE@EXAMPLE.COM ",
            "phone": " 555-0100 ",
        },
    )
    assert created.status_code == 201
    assert created.headers["Location"].endswith("/api/v1/clients/1")
    client_id = created.json["data"]["id"]
    assert created.json["data"]["name"] == "Grace Hopper"
    assert created.json["data"]["email"] == "grace@example.com"

    fetched = client.get("/api/v1/clients/{}".format(client_id))
    assert fetched.status_code == 200
    assert fetched.json["data"]["company"] == "Navy"

    updated = client.patch(
        "/api/v1/clients/{}".format(client_id),
        json={"name": "Grace Brewster Hopper"},
    )
    assert updated.status_code == 200
    assert updated.json["data"]["name"] == "Grace Brewster Hopper"
    assert updated.json["data"]["company"] == "Navy"

    deleted = client.delete("/api/v1/clients/{}".format(client_id))
    assert deleted.status_code == 204
    assert client.get("/api/v1/clients/{}".format(client_id)).status_code == 404

    with app.app_context():
        actions = db.session.execute(
            db.select(ActivityLog.action).order_by(ActivityLog.id)
        ).scalars().all()
        assert actions == ["client.created", "client.updated", "client.deleted"]


def test_api_rejects_invalid_json_fields(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        user_id = user.id
    login_as(client, user_id)

    missing_name = client.post("/api/v1/clients", json={"company": "Navy"})
    wrong_type = client.post(
        "/api/v1/clients",
        json={"name": "Grace Hopper", "phone": 42},
    )
    unknown_field = client.post(
        "/api/v1/clients",
        json={"name": "Grace Hopper", "role": "admin"},
    )
    invalid_email = client.post(
        "/api/v1/clients",
        json={"name": "Grace Hopper", "email": "invalid"},
    )
    not_json = client.post(
        "/api/v1/clients",
        data="name=Grace",
        content_type="text/plain",
    )

    assert missing_name.status_code == 400
    assert "name" in missing_name.json["errors"]
    assert wrong_type.status_code == 400
    assert "phone" in wrong_type.json["errors"]
    assert unknown_field.status_code == 400
    assert invalid_email.status_code == 400
    assert not_json.status_code == 400
    assert not_json.json["errors"]["body"]


def test_api_enforces_user_ownership_and_admin_access(app, client):
    with app.app_context():
        owner = create_user("owner@example.com")
        other = create_user("other@example.com")
        admin = create_user("admin@example.com", role=UserRole.ADMIN)
        record = Client(name="Private Client", owner_id=owner.id)
        db.session.add(record)
        db.session.commit()
        client_id = record.id
        other_id, admin_id = other.id, admin.id

    login_as(client, other_id)
    assert client.get("/api/v1/clients/{}".format(client_id)).status_code == 404
    assert client.patch(
        "/api/v1/clients/{}".format(client_id),
        json={"name": "Stolen"},
    ).status_code == 404
    assert client.delete("/api/v1/clients/{}".format(client_id)).status_code == 404
    assert client.get("/api/v1/clients").json == {"data": []}

    admin_client = app.test_client()
    login_as(admin_client, admin_id)
    listing = admin_client.get("/api/v1/clients")
    assert listing.status_code == 200
    assert listing.json["data"][0]["name"] == "Private Client"


def test_api_state_changing_requests_require_csrf_token(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        user_id = user.id
    login_as(client, user_id)
    app.config["WTF_CSRF_ENABLED"] = True

    rejected = client.post("/api/v1/clients", json={"name": "No token"})
    assert rejected.status_code == 400
    assert rejected.json["error"] == "CSRF validation failed."

    token_response = client.get("/api/v1/csrf-token")
    token = token_response.json["csrf_token"]
    accepted = client.post(
        "/api/v1/clients",
        json={"name": "With token"},
        headers={"X-CSRFToken": token},
    )
    assert accepted.status_code == 201
