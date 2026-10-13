from crm.extensions import db
from crm.models import Client, Note, User


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


def test_client_detail_lists_notes_with_author(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        record = Client(name="Grace Hopper", owner_id=user.id)
        db.session.add(record)
        db.session.flush()
        note = Note(
            body="Discussed the project timeline.",
            client_id=record.id,
            author_id=user.id,
        )
        db.session.add(note)
        db.session.commit()
        user_id, client_id = user.id, record.id
    login_as(client, user_id)

    response = client.get("/clients/{}".format(client_id))

    assert response.status_code == 200
    assert b"Discussed the project timeline." in response.data
    assert b"Ada Lovelace" in response.data
    assert b"Add a note" in response.data


def test_owner_can_add_note_to_client(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        record = Client(name="Grace Hopper", owner_id=user.id)
        db.session.add(record)
        db.session.commit()
        user_id, client_id = user.id, record.id
    login_as(client, user_id)

    response = client.post(
        "/clients/{}/notes".format(client_id),
        data={"body": "  Send the proposal by Friday.  "},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Send the proposal by Friday." in response.data
    with app.app_context():
        saved_note = db.session.execute(
            db.select(Note).where(Note.client_id == client_id)
        ).scalar_one()
        assert saved_note.body == "Send the proposal by Friday."
        assert saved_note.author_id == user_id


def test_note_submission_rejects_empty_or_oversized_content(app, client):
    with app.app_context():
        user = create_user("ada@example.com")
        record = Client(name="Grace Hopper", owner_id=user.id)
        db.session.add(record)
        db.session.commit()
        user_id, client_id = user.id, record.id
    login_as(client, user_id)

    empty_response = client.post(
        "/clients/{}/notes".format(client_id),
        data={"body": "  "},
    )
    oversized_response = client.post(
        "/clients/{}/notes".format(client_id),
        data={"body": "x" * 5001},
    )

    assert empty_response.status_code == 200
    assert b"This field is required" in empty_response.data
    assert oversized_response.status_code == 200
    assert b"cannot be longer than 5000 characters" in oversized_response.data
    with app.app_context():
        assert db.session.execute(db.select(Note)).scalars().all() == []


def test_user_cannot_add_note_to_another_users_client(app, client):
    with app.app_context():
        owner = create_user("owner@example.com")
        other = create_user("other@example.com", first_name="Katherine")
        record = Client(name="Private Contact", owner_id=owner.id)
        db.session.add(record)
        db.session.commit()
        other_id, client_id = other.id, record.id
    login_as(client, other_id)

    response = client.post(
        "/clients/{}/notes".format(client_id),
        data={"body": "Unauthorized note"},
    )

    assert response.status_code == 404
    with app.app_context():
        assert db.session.execute(db.select(Note)).scalars().all() == []
