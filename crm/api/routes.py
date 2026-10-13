from __future__ import annotations

from flask import jsonify, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf.csrf import CSRFError, generate_csrf
from werkzeug.datastructures import MultiDict

from crm.activity import log_activity
from crm.api import api_blueprint
from crm.auth.permissions import can_manage_client, is_admin
from crm.clients.forms import ClientForm
from crm.extensions import db
from crm.models import Client, User


def _serialize_client(client: Client) -> dict:
    return {
        "id": client.id,
        "name": client.name,
        "company": client.company,
        "email": client.email,
        "phone": client.phone,
        "owner_id": client.owner_id,
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }


def _client_from_request(existing: Client | None = None):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, {"body": ["A JSON object is required."]}

    allowed_fields = {"name", "company", "email", "phone"}
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        return None, {
            "body": ["Unsupported fields: {}.".format(", ".join(sorted(unknown_fields)))]
        }
    if existing is None and "name" not in payload:
        return None, {"name": ["This field is required."]}

    values = {
        "name": existing.name if existing else "",
        "company": existing.company if existing else "",
        "email": existing.email if existing else "",
        "phone": existing.phone if existing else "",
    }
    for key, value in payload.items():
        if value is not None and not isinstance(value, str):
            return None, {key: ["Must be a string."]}
        values[key] = value or ""

    form = ClientForm(
        formdata=MultiDict(values),
        meta={"csrf": False},
    )
    if not form.validate():
        return None, form.errors

    return {
        "name": form.name.data,
        "company": form.company.data,
        "email": form.email.data,
        "phone": form.phone.data,
    }, None


@api_blueprint.before_request
def require_session_authentication():
    if request.endpoint in {"api.csrf_token", "api.login"}:
        return None
    if not current_user.is_authenticated:
        return jsonify(error="Authentication required."), 401
    return None


@api_blueprint.errorhandler(CSRFError)
def handle_csrf_error(error: CSRFError):
    return jsonify(error="CSRF validation failed.", detail=error.description), 400


@api_blueprint.get("/csrf-token")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@api_blueprint.post("/auth/login")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="A JSON object is required."), 400

    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify(error="Email and password are required."), 400

    user = db.session.execute(
        db.select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()
    if user is None or not user.check_password(password):
        return jsonify(error="Invalid email or password."), 401

    login_user(user)
    return jsonify(user={"id": user.id, "email": user.email, "role": user.role.value})


@api_blueprint.post("/auth/logout")
def logout():
    logout_user()
    return "", 204


@api_blueprint.get("/clients")
def list_clients():
    query = db.select(Client)
    if not is_admin(current_user):
        query = query.where(Client.owner_id == current_user.id)

    clients = db.session.execute(
        query.order_by(Client.name, Client.id)
    ).scalars().all()
    return jsonify(data=[_serialize_client(client) for client in clients])


@api_blueprint.post("/clients")
def create_client():
    values, errors = _client_from_request()
    if errors:
        return jsonify(errors=errors), 400

    client = Client(**values, owner_id=current_user.id)
    db.session.add(client)
    db.session.flush()
    log_activity(
        "client.created",
        "client",
        client.id,
        client,
        "Added client {}".format(client.name),
    )
    db.session.commit()
    return (
        jsonify(data=_serialize_client(client)),
        201,
        {"Location": url_for("api.get_client", client_id=client.id)},
    )


@api_blueprint.get("/clients/<int:client_id>")
def get_client(client_id: int):
    client = db.session.get(Client, client_id)
    if client is None or not can_manage_client(current_user, client):
        return jsonify(error="Client not found."), 404
    return jsonify(data=_serialize_client(client))


@api_blueprint.patch("/clients/<int:client_id>")
def update_client(client_id: int):
    client = db.session.get(Client, client_id)
    if client is None or not can_manage_client(current_user, client):
        return jsonify(error="Client not found."), 404

    values, errors = _client_from_request(existing=client)
    if errors:
        return jsonify(errors=errors), 400

    for field, value in values.items():
        setattr(client, field, value)
    log_activity(
        "client.updated",
        "client",
        client.id,
        client,
        "Updated client {}".format(client.name),
    )
    db.session.commit()
    return jsonify(data=_serialize_client(client))


@api_blueprint.delete("/clients/<int:client_id>")
def delete_client(client_id: int):
    client = db.session.get(Client, client_id)
    if client is None or not can_manage_client(current_user, client):
        return jsonify(error="Client not found."), 404

    log_activity(
        "client.deleted",
        "client",
        client.id,
        client,
        "Deleted client {}".format(client.name),
    )
    db.session.delete(client)
    db.session.commit()
    return "", 204
