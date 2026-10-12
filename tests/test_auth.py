from crm.extensions import db
from crm.models import User, UserRole


def test_registration_page_is_available(client):
    response = client.get("/auth/register")

    assert response.status_code == 200
    assert b"Create your account" in response.data


def test_registration_creates_user_with_normalized_email_and_hashed_password(
    app, client
):
    response = client.post(
        "/auth/register",
        data={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "  ADA@example.com ",
            "password": "correct-horse-battery-staple",
            "password_confirmation": "correct-horse-battery-staple",
        },
        follow_redirects=True,
    )

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "ada@example.com")
        ).scalar_one()

        assert user.first_name == "Ada"
        assert user.last_name == "Lovelace"
        assert user.role == UserRole.USER
        assert user.password_hash != "correct-horse-battery-staple"
        assert user.check_password("correct-horse-battery-staple")

    assert response.status_code == 200
    assert b"Account created" in response.data


def test_registration_rejects_duplicate_email_case_insensitively(app, client):
    with app.app_context():
        user = User(first_name="Ada", last_name="Lovelace", email="ada@example.com")
        user.set_password("correct-horse-battery-staple")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/register",
        data={
            "first_name": "Augusta",
            "last_name": "King",
            "email": "ADA@example.com",
            "password": "another-secure-password",
            "password_confirmation": "another-secure-password",
        },
    )

    assert response.status_code == 200
    assert b"already exists" in response.data


def test_registration_rejects_short_or_mismatched_password(client):
    response = client.post(
        "/auth/register",
        data={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "password": "short",
            "password_confirmation": "different",
        },
    )

    assert response.status_code == 200
    assert b"at least 12 characters" in response.data
    assert b"Passwords must match" in response.data


def test_login_authenticates_user_and_uses_safe_next_url(app, client):
    with app.app_context():
        user = User(first_name="Ada", last_name="Lovelace", email="ada@example.com")
        user.set_password("correct-horse-battery-staple")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/login?next=/private/page",
        data={
            "email": " ADA@example.com ",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/private/page")
    with client:
        response = client.get("/auth/welcome")
        assert response.status_code == 200
        assert b"Ada Lovelace" in response.data


def test_login_rejects_invalid_credentials_without_disclosing_account_status(
    app, client
):
    with app.app_context():
        user = User(first_name="Ada", last_name="Lovelace", email="ada@example.com")
        user.set_password("correct-horse-battery-staple")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/login",
        data={"email": "ada@example.com", "password": "incorrect-password"},
    )

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_ignores_external_next_url(app, client):
    with app.app_context():
        user = User(first_name="Ada", last_name="Lovelace", email="ada@example.com")
        user.set_password("correct-horse-battery-staple")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/login?next=https://attacker.example",
        data={
            "email": "ada@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/welcome")


def test_logout_clears_authenticated_session(app, client):
    with app.app_context():
        user = User(first_name="Ada", last_name="Lovelace", email="ada@example.com")
        user.set_password("correct-horse-battery-staple")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client:
        with client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True

        response = client.post("/auth/logout")

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/auth/login")
        with client.session_transaction() as session:
            assert "_user_id" not in session
