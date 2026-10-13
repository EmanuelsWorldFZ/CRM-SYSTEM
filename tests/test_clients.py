from crm.extensions import db
from crm.models import Client, User


def create_user(email, first_name="Ada"):
    user = User(first_name=first_name, last_name="Lovelace", email=email)
    user.set_password("correct-horse-battery-staple")
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_client_list_requires_authentication(client):
    response = client.get("/clients/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login?next=%2Fclients%2F")


def test_create_client_normalizes_optional_contact_fields(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        user_id = user.id
    login_as(client, user_id)

    response = client.post(
        "/clients/new",
        data={
            "name": "  Grace Hopper ",
            "company": "  Navy ",
            "email": " GRACE@EXAMPLE.COM ",
            "phone": " 555-0100 ",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Grace Hopper" in response.data
    with app.app_context():
        saved = db.session.execute(
            db.select(Client).where(Client.owner_id == user_id)
        ).scalar_one()
        assert saved.name == "Grace Hopper"
        assert saved.company == "Navy"
        assert saved.email == "grace@example.com"
        assert saved.phone == "555-0100"


def test_owner_can_view_update_and_delete_client(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        record = Client(name="Grace Hopper", owner_id=user.id)
        db.session.add(record)
        db.session.commit()
        user_id, client_id = user.id, record.id
    login_as(client, user_id)

    detail = client.get("/clients/{}".format(client_id))
    assert detail.status_code == 200
    assert b"Grace Hopper" in detail.data

    update = client.post(
        "/clients/{}/edit".format(client_id),
        data={
            "name": "Grace Brewster Hopper",
            "company": "US Navy",
            "email": "",
            "phone": "",
        },
        follow_redirects=True,
    )
    assert update.status_code == 200
    assert b"Grace Brewster Hopper" in update.data

    delete = client.post("/clients/{}/delete".format(client_id))
    assert delete.status_code == 302
    with app.app_context():
        assert db.session.get(Client, client_id) is None


def test_user_cannot_access_another_users_client(app, client):
    with app.app_context():
        owner = create_user("owner@example.com")
        other = create_user("other@example.com", first_name="Katherine")
        record = Client(name="Private Contact", owner_id=owner.id)
        db.session.add(record)
        db.session.commit()
        other_id, client_id = other.id, record.id
    login_as(client, other_id)

    assert client.get("/clients/{}".format(client_id)).status_code == 404
    assert client.get("/clients/{}/edit".format(client_id)).status_code == 404
    assert client.post("/clients/{}/delete".format(client_id)).status_code == 404
    listing = client.get("/clients/")
    assert b"Private Contact" not in listing.data


def test_create_client_rejects_invalid_email(client, app):
    with app.app_context():
        user = create_user("ada@example.com")
        user_id = user.id
    login_as(client, user_id)

    response = client.post(
        "/clients/new",
        data={"name": "Grace Hopper", "email": "not-an-email"},
    )

    assert response.status_code == 200
    assert b"Invalid email address" in response.data
