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
  api/           Versioned, session-authenticated JSON API
  clients/       Owner-scoped client management, search, and filtering
  dashboard/     Authenticated workspace overview
  activity.py    Client and note audit event recording
  models/        SQLAlchemy entities
  templates/     Shared and blueprint-specific Jinja templates
  __init__.py    Application factory and CLI commands
  config.py      Environment-based configuration
  extensions.py  SQLAlchemy, Flask-Login, and CSRF instances
tests/
  conftest.py
  test_auth.py
  test_clients.py
  test_notes.py
  test_authorization.py
  test_activity.py
  test_api.py
```

## Planned database schema

- `users`: first and last name, canonical unique email, password hash, role
  (`admin` or `user`), and creation timestamp.
- `clients`: client contact and company details, owner (`users.id`), and
  creation/update timestamps.
- `notes`: note body, client (`clients.id`), author (`users.id`), and timestamp.
- `activity_logs`: actor, action, target type/id, client/owner snapshots, and
  timestamp; records remain available after a client is deleted.

Clients belong to a user; notes belong to a client and record their author.
Foreign keys enforce those relationships. Passwords are stored only as
Werkzeug-generated hashes. Registration, login, the dashboard, role-based
client access, client notes, activity logs, and the versioned client API are
implemented.

## Development roadmap

1. User registration with validated input, password hashing, and tests (complete).
2. Login/logout and authenticated session handling (complete).
3. Dashboard with authenticated account overview (complete).
4. Client CRUD, ownership enforcement, search, and company filtering (complete).
5. Add and view client notes (complete).
6. Admin/User authorization for client records (complete).
7. Activity logging for client and note changes (complete).
8. Versioned REST API for clients (complete).
9. Broader test coverage and production hardening.

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

New registrations receive the `user` role. Assign an administrator from a
trusted shell with `flask --app crm:create_app set-user-role EMAIL admin`.
Admins can view, edit, and delete all clients; regular users are limited to
their own records.

## REST API

The `/api/v1` endpoints use the same session login and role-based client access
as the web app. Fetch a CSRF token first and send it as `X-CSRFToken` with
state-changing requests. JSON responses use a `data` object or array; invalid
input returns `400`, unauthenticated requests return `401`, and inaccessible
client IDs return `404`.

Endpoints: `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`,
`GET /api/v1/clients`, `POST /api/v1/clients`,
`GET /api/v1/clients/<id>`, `PATCH /api/v1/clients/<id>`, and
`DELETE /api/v1/clients/<id>`.

Example flow using curl's cookie jar:

```bash
curl -c cookies.txt http://127.0.0.1:5000/api/v1/csrf-token
```

Copy the returned `csrf_token` and send it as the `X-CSRFToken` header along
with the cookie jar to the JSON login endpoint. Repeat the token request after
login, then include the returned token and cookie jar on POST, PATCH, and
DELETE requests.
