from flask import redirect, abort, render_template, url_for, session, request, jsonify
from flask_login import current_user

from ... import db
from .. import storage

from ..models import (
    CryovialBox,
    SampleToCryovialBox,
    FixedColdStorage,
    Room,
    Site,
    FixedColdStorageShelf,
    CryovialBoxToFixedColdStorageShelf,
)
from ..forms import NewCryovialBoxForm, SampleToBoxForm

from ...auth.models import User
from ...sample.models import Sample


@storage.route("/cryobox")
def cryobox_index():
    boxes = (
        db.session.query(CryovialBox, User)
        .filter(CryovialBox.author_id == User.id)
        .all()
    )
    return render_template("storage/cryobox/index.html", boxes=boxes)


@storage.route("/cryobox/new", methods=["GET", "POST"])
def add_cryobox():
    storage_options = (
        db.session.query(FixedColdStorageShelf, FixedColdStorage, Room, Site)
        .filter(FixedColdStorageShelf.storage_id == FixedColdStorage.id)
        .filter(Room.id == FixedColdStorage.room_id)
        .filter(Site.id == Room.id)
        .all()
    )

    form = NewCryovialBoxForm(storage_options)

    if form.validate_on_submit():

        cb = CryovialBox(
            serial=form.serial.data,
            num_rows=form.num_rows.data,
            num_cols=form.num_cols.data,
            author_id=current_user.id,
        )

        db.session.add(cb)
        db.session.flush()

        cbfcs = CryovialBoxToFixedColdStorageShelf(
            box_id=cb.id, shelf_id=int(form.lts.data), author_id=current_user.id
        )

        db.session.add(cbfcs)

        db.session.commit()

        return redirect(url_for("storage.cryobox_index"))

    return render_template("storage/cryobox/new.html", form=form)


@storage.route("/cryobox/view/LIMBCRB-<cryo_id>")
def view_cryobox(cryo_id):
    cryo = (
        db.session.query(CryovialBox).filter(CryovialBox.id == cryo_id).first_or_404()
    )
    return render_template("storage/cryobox/view.html", cryo=cryo)


@storage.route("/cryobox/view/LIMBCRB-<cryo_id>/data")
def view_cryobox_api(cryo_id):
    cryo = (
        db.session.query(CryovialBox).filter(CryovialBox.id == cryo_id).first_or_404()
    )

    samples = (
        db.session.query(SampleToCryovialBox, Sample, User)
        .filter(SampleToCryovialBox.box_id == cryo_id)
        .filter(Sample.id == SampleToCryovialBox.sample_id)
        .filter(Sample.author_id == User.id)
        .all()
    )

    data = {}
    for position, sample, user in samples:
        data["%i_%i" % (position.row, position.col)] = {
            "id": sample.id,
            "url": url_for("sample.view", sample_id=sample.id, _external=True),
        }

    return jsonify(data), 201, {"Content-Type": "application/json"}


@storage.route(
    "/cryobox/add/sample/LIMCRB-<cryo_id>/<row>_<col>", methods=["GET", "POST"]
)
def add_cryobox_sample(cryo_id, row, col):
    cryo = (
        db.session.query(CryovialBox).filter(CryovialBox.id == cryo_id).first_or_404()
    )

    samples = db.session.query(Sample).all()

    form = SampleToBoxForm(samples)

    if form.validate_on_submit():
        scb = SampleToCryovialBox(
            sample_id=form.samples.data,
            box_id=cryo_id,
            col=col,
            row=row,
            author_id=current_user.id,
        )

        db.session.add(scb)
        db.session.commit()

        return redirect(url_for("storage.view_cryobox", cryo_id=cryo_id))

    return render_template(
        "storage/cryobox/sample_to_box.html", cryo=cryo, form=form, row=row, col=col
    )
