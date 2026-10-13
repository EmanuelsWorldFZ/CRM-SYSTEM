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


def test_client_and_note_changes_create_audit_records(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        user_id = user.id
    login_as(client, user_id)

    created = client.post(
        "/clients/new",
        data={"name": "Grace Hopper", "company": "Navy"},
    )
    assert created.status_code == 302
    with app.app_context():
        record = db.session.execute(
            db.select(Client).where(Client.owner_id == user_id)
        ).scalar_one()
        client_id = record.id

    client.post(
        "/clients/{}/edit".format(client_id),
        data={
            "name": "Grace Brewster Hopper",
            "company": "Navy",
            "email": "",
            "phone": "",
        },
    )
    client.post(
        "/clients/{}/notes".format(client_id),
        data={"body": "Discussed the next project."},
    )
    client.post("/clients/{}/delete".format(client_id))

    with app.app_context():
        events = db.session.execute(
            db.select(ActivityLog).order_by(ActivityLog.id)
        ).scalars().all()
        assert [event.action for event in events] == [
            "client.created",
            "client.updated",
            "note.created",
            "client.deleted",
        ]
        assert events[0].actor_name == "Ada Example"
        assert events[0].owner_id == user_id
        assert events[-1].client_name == "Grace Brewster Hopper"
        assert events[-1].client_id == client_id


def test_dashboard_shows_only_current_users_activity(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        other = create_user("other@example.com")
        events = [
            ActivityLog(
                actor_id=user.id,
                actor_name="Ada Example",
                owner_id=user.id,
                action="client.created",
                target_type="client",
                target_id=1,
                client_id=1,
                client_name="Ada Client",
                summary="Added client Ada Client",
            ),
            ActivityLog(
                actor_id=other.id,
                actor_name="Other Example",
                owner_id=other.id,
                action="client.created",
                target_type="client",
                target_id=2,
                client_id=2,
                client_name="Private Client",
                summary="Added client Private Client",
            ),
        ]
        db.session.add_all(events)
        db.session.commit()
        user_id = user.id
    login_as(client, user_id)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Added client Ada Client" in response.data
    assert b"Private Client" not in response.data


def test_admin_dashboard_shows_workspace_activity(app, client):
    with app.app_context():
        owner = create_user("owner@example.com")
        admin = create_user("admin@example.com", role=UserRole.ADMIN)
        db.session.add(
            ActivityLog(
                actor_id=owner.id,
                actor_name="Owner Example",
                owner_id=owner.id,
                action="client.created",
                target_type="client",
                target_id=1,
                client_id=1,
                client_name="Owner Client",
                summary="Added client Owner Client",
            )
        )
        db.session.commit()
        admin_id = admin.id
    login_as(client, admin_id)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Added client Owner Client" in response.data
    assert b"Owner Client" in response.data
