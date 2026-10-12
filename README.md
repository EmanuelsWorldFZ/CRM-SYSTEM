# Portfolio CRM

A Flask CRM built to demonstrate authentication, relational data modeling,
authorization, API design, and automated testing.

## Architecture

The application uses an application factory and separate Flask blueprints.
Configuration and shared extensions are kept outside route modules; database
models live in `crm/models`; feature-specific forms, routes, and templates are
grouped with their blueprint. Pytest exercises the app through its test client.

```text
crm/
  auth/          Registration and login/logout
  models/        SQLAlchemy entities
  templates/     Shared and blueprint-specific Jinja templates
  __init__.py    Application factory and CLI commands
  config.py      Environment-based configuration
  extensions.py  SQLAlchemy, Flask-Login, and CSRF instances
tests/
  conftest.py
  test_auth.py
```

## Planned database schema

- `users`: first and last name, canonical unique email, password hash, role
  (`admin` or `user`), and creation timestamp.
- `clients`: client contact and company details, owner (`users.id`), and
  creation/update timestamps.
- `notes`: note body, client (`clients.id`), author (`users.id`), and timestamp.
- `activity_logs`: actor (`users.id`), action, target type/id, and timestamp.

Clients belong to a user; notes belong to a client and record their author.
Foreign keys enforce those relationships. Passwords are stored only as
Werkzeug-generated hashes. The first feature implements the user table only;
the remaining entities arrive with their respective features.

## Development roadmap

1. User registration with validated input, password hashing, and tests (complete).
2. Login/logout and authenticated session handling (complete).
3. Dashboard.
4. Client CRUD and ownership enforcement.
5. Client notes.
6. Search and filtering.
7. Admin/User authorization.
8. Activity logging.
9. Versioned REST API.
10. Broader test coverage and production hardening.

## Run locally

Use Python 3.9 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Replace the `SECRET_KEY` placeholder in `.env` with a fresh random value
(generate one with `python -c "import secrets; print(secrets.token_hex(32))"`).
Then initialize the database and start Flask:

```bash
flask --app crm:create_app init-db
flask --app crm:create_app run --debug
```

Open `http://127.0.0.1:5000/auth/register`. Run tests with `pytest`.
