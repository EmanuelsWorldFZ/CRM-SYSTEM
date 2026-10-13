from crm.extensions import db
from crm.models import Client, User, UserRole


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


def test_admin_can_list_and_manage_clients_across_users(app, client):
    with app.app_context():
        owner = create_user("owner@example.com")
        admin = create_user("admin@example.com", role=UserRole.ADMIN)
        record = Client(
            name="Private Contact",
            company="Example Corp",
            owner_id=owner.id,
        )
        db.session.add(record)
        db.session.commit()
        admin_id, client_id = admin.id, record.id
    login_as(client, admin_id)

    listing = client.get("/clients/")
    assert listing.status_code == 200
    assert b"Private Contact" in listing.data
    assert b"Owner Example" in listing.data

    detail = client.get("/clients/{}".format(client_id))
    assert detail.status_code == 200
    assert b"Record owner" in detail.data
    assert b"Owner Example" in detail.data

    update = client.post(
        "/clients/{}/edit".format(client_id),
        data={
            "name": "Updated Contact",
            "company": "Example Corp",
            "email": "",
            "phone": "",
        },
        follow_redirects=True,
    )
    assert update.status_code == 200
    assert b"Updated Contact" in update.data

    delete = client.post("/clients/{}/delete".format(client_id))
    assert delete.status_code == 302
    with app.app_context():
        assert db.session.get(Client, client_id) is None


def test_admin_can_add_note_to_another_users_client(app, client):
    with app.app_context():
        owner = create_user("owner@example.com")
        admin = create_user("admin@example.com", role=UserRole.ADMIN)
        record = Client(name="Owner Contact", owner_id=owner.id)
        db.session.add(record)
        db.session.commit()
        admin_id, client_id = admin.id, record.id
    login_as(client, admin_id)

    response = client.post(
        "/clients/{}/notes".format(client_id),
        data={"body": "Admin follow-up"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Admin follow-up" in response.data


def test_role_assignment_cli_updates_existing_user(app):
    with app.app_context():
        user = create_user("new-admin@example.com")
        user_id = user.id

    result = app.test_cli_runner().invoke(
        args=["set-user-role", "NEW-ADMIN@example.com", "admin"]
    )

    assert result.exit_code == 0
    assert "Updated new-admin@example.com to role admin." in result.output
    with app.app_context():
        assert db.session.get(User, user_id).role == UserRole.ADMIN


def test_role_assignment_cli_rejects_unknown_user(app):
    result = app.test_cli_runner().invoke(
        args=["set-user-role", "missing@example.com", "admin"]
    )

    assert result.exit_code != 0
    assert "No user found with that email address." in result.output


def test_registration_cannot_assign_admin_role(client, app):
    response = client.post(
        "/auth/register",
        data={
            "first_name": "Eve",
            "last_name": "Example",
            "email": "eve@example.com",
            "password": "correct-horse-battery-staple",
            "password_confirmation": "correct-horse-battery-staple",
            "role": "admin",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "eve@example.com")
        ).scalar_one()
        assert user.role == UserRole.USER
