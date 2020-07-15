from flask import redirect, abort, render_template, url_for, session, request, jsonify, flash
from flask_login import current_user, login_required

from ... import db
from .. import storage

from ..views.shelf import BasicShelfView
from ...auth.models import User
from ..forms import LongTermColdStorageForm, NewShelfForm
from ..models import FixedColdStorageShelf, FixedColdStorage

from uuid import uuid4

from ..views import LTSView, BasicLTSView


@storage.route("/lts/LIMBLTS-<lts_id>", methods=["GET"])
@login_required
def view_lts(lts_id: int):
    lts = LTSView(lts_id)
    return render_template("/storage/lts/view.html", lts=lts)

@storage.route("/lts/LIMBLTS-<lts_id>/add_shelf", methods=["GET", "POST"])
@login_required
def add_shelf(lts_id: int):
    lts = BasicLTSView(lts_id)

    form = NewShelfForm()

    if form.validate_on_submit():
        shelf = FixedColdStorageShelf(
            name=form.name.data,
            # Generate an UUID :)
            uuid=uuid4(),
            description=form.description.data,
            storage_id=lts_id,
            author_id=current_user.id,
        )

        db.session.add(shelf)
        db.session.commit()

        return redirect(url_for("storage.view_lts", lts_id=lts_id))

    return render_template("/storage/shelf/new.html", form=form, lts=lts)

@storage.route("/lts/LIMBLTS-<lts_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lts(lts_id):
    lts = LTSView(lts_id)
    form = LongTermColdStorageForm()

    if form.validate_on_submit():
        s = db.session.query(FixedColdStorage).filter(FixedColdStorage.id == lts_id).first_or_404()
        s.manufacturer = form.manufacturer.data
        # TODO: Fix this annoying issue wherein forms aren't being validated against enumerated types properly.
        # s.temperature = form.temperature.data,
        s.serial_number = form.serial_number.data,
        s.type = form.type.data

        s.author_id = current_user.id

        db.session.commit()
        flash("Successfully edited!")
        return redirect(url_for("storage.view_lts", lts_id=lts_id))

    form.manufacturer.data = lts["manufacturer"]
    form.temperature.data = lts["temperature"]
    form.serial_number.data = lts["serial_number"]
    form.type.data = lts["type"]

    return render_template("storage/lts/edit.html", lts=lts, form=form)