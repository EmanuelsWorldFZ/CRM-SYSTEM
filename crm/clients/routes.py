from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from crm.activity import log_activity
from crm.auth.permissions import can_manage_client, is_admin
from crm.clients import clients_blueprint
from crm.clients.forms import ClientForm
from crm.clients.note_forms import NoteForm
from crm.extensions import db
from crm.models import Client, Note


def _owned_client_or_404(client_id: int) -> Client:
    client = db.session.get(Client, client_id)
    if client is None or not can_manage_client(current_user, client):
        abort(404)
    return client


@clients_blueprint.get("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    company_filter = request.args.get("company", "").strip()

    query = db.select(Client)
    if not is_admin(current_user):
        query = query.where(Client.owner_id == current_user.id)
    if search:
        escaped_search = (
            search.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        pattern = "%{}%".format(escaped_search)
        query = query.where(
            or_(
                Client.name.ilike(pattern, escape="\\"),
                Client.company.ilike(pattern, escape="\\"),
                Client.email.ilike(pattern, escape="\\"),
                Client.phone.ilike(pattern, escape="\\"),
            )
        )
    if company_filter:
        query = query.where(Client.company == company_filter)

    clients = db.session.execute(
        query.order_by(Client.name, Client.id)
    ).scalars().all()
    company_query = db.select(Client.company).where(
        Client.company.is_not(None),
        Client.company != "",
    )
    if not is_admin(current_user):
        company_query = company_query.where(Client.owner_id == current_user.id)
    companies = db.session.execute(
        company_query.distinct().order_by(Client.company)
    ).scalars().all()
    return render_template(
        "clients/index.html",
        clients=clients,
        companies=companies,
        search=search,
        company_filter=company_filter,
    )


@clients_blueprint.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            company=form.company.data,
            email=form.email.data,
            phone=form.phone.data,
            owner_id=current_user.id,
        )
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
        flash("Client added successfully.", "success")
        return redirect(url_for("clients.index"))

    return render_template("clients/form.html", form=form, title="Add a client")


@clients_blueprint.get("/<int:client_id>")
@login_required
def detail(client_id: int):
    client = _owned_client_or_404(client_id)
    note_form = NoteForm()
    return render_template(
        "clients/detail.html",
        client=client,
        note_form=note_form,
    )


@clients_blueprint.post("/<int:client_id>/notes")
@login_required
def add_note(client_id: int):
    client = _owned_client_or_404(client_id)
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(
            body=form.body.data,
            client_id=client.id,
            author_id=current_user.id,
        )
        db.session.add(note)
        db.session.flush()
        log_activity(
            "note.created",
            "note",
            note.id,
            client,
            "Added a note to {}".format(client.name),
        )
        db.session.commit()
        flash("Note added successfully.", "success")
        return redirect(url_for("clients.detail", client_id=client.id))

    return render_template(
        "clients/detail.html",
        client=client,
        note_form=form,
    )


@clients_blueprint.route("/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit(client_id: int):
    client = _owned_client_or_404(client_id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        form.populate_obj(client)
        log_activity(
            "client.updated",
            "client",
            client.id,
            client,
            "Updated client {}".format(client.name),
        )
        db.session.commit()
        flash("Client updated successfully.", "success")
        return redirect(url_for("clients.detail", client_id=client.id))

    return render_template(
        "clients/form.html",
        form=form,
        title="Edit client",
        client=client,
    )


@clients_blueprint.post("/<int:client_id>/delete")
@login_required
def delete(client_id: int):
    client = _owned_client_or_404(client_id)
    log_activity(
        "client.deleted",
        "client",
        client.id,
        client,
        "Deleted client {}".format(client.name),
    )
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted.", "success")
    return redirect(url_for("clients.index"))
