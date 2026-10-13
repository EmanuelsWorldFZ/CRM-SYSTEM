from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from crm.clients import clients_blueprint
from crm.clients.forms import ClientForm
from crm.extensions import db
from crm.models import Client


def _owned_client_or_404(client_id: int) -> Client:
    client = db.session.execute(
        db.select(Client).where(
            Client.id == client_id,
            Client.owner_id == current_user.id,
        )
    ).scalar_one_or_none()
    if client is None:
        abort(404)
    return client


@clients_blueprint.get("/")
@login_required
def index():
    clients = db.session.execute(
        db.select(Client)
        .where(Client.owner_id == current_user.id)
        .order_by(Client.name, Client.id)
    ).scalars()
    return render_template("clients/index.html", clients=clients)


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
        db.session.commit()
        flash("Client added successfully.", "success")
        return redirect(url_for("clients.index"))

    return render_template("clients/form.html", form=form, title="Add a client")


@clients_blueprint.get("/<int:client_id>")
@login_required
def detail(client_id: int):
    client = _owned_client_or_404(client_id)
    return render_template("clients/detail.html", client=client)


@clients_blueprint.route("/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit(client_id: int):
    client = _owned_client_or_404(client_id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        form.populate_obj(client)
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
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted.", "success")
    return redirect(url_for("clients.index"))
