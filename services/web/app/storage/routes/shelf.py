from flask import redirect, abort, render_template, url_for, session, request, jsonify
from flask_login import current_user, login_required

from ... import db
from .. import storage


from ..models import (
    Site,
    Room,
    FixedColdStorage,
    FixedColdStorageShelf,
    SampleToFixedColdStorageShelf,
    CryovialBox,
    CryovialBoxToFixedColdStorageShelf,
    SampleToCryovialBox,
)
from ...sample.models import Sample

from ...misc.models import Address
from ...auth.models import User
from ..forms import NewCryovialBoxForm, SampleToBoxForm

from ..views import ShelfView

from ...misc import chunks


@storage.route("/shelves/view/LIMBSHF-<id>")
@login_required
def view_shelf(id):
    shelf = ShelfView(id)

    # Conversion to make it renderable
    shelf["cryoboxes"] = chunks([x for x in shelf["cryoboxes"].items()], 4)

    return render_template(
        "storage/shelf/view.html", shelf=shelf
    )
    

@storage.route("/shelves/add_cryobox/LIMBSHF-<shelf_id>", methods=["GET", "POST"])
@login_required
def add_cryobox(shelf_id):
    shelf = (
        db.session.query(FixedColdStorageShelf)
        .filter(FixedColdStorageShelf.id == shelf_id)
        .first_or_404()
    )
    form = NewCryovialBoxForm()

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
            box_id=cb.id, shelf_id=shelf_id, author_id=current_user.id
        )

        db.session.add(cbfcs)

        db.session.commit()

        return redirect(url_for("storage.view_shelf", id=shelf.id))

    return render_template("storage/cryobox/new.html", form=form, shelf=shelf)


@storage.route("/shelves/assign_sample/LIMBSHF-<shelf_id>", methods=["GET", "POST"])
@login_required
def assign_sample_to_shelf(shelf_id):
    shelf = (
        db.session.query(FixedColdStorageShelf)
        .filter(FixedColdStorageShelf.id == shelf_id)
        .first_or_404()
    )
    samples = db.session.query(Sample).all()

    form = SampleToBoxForm(samples)
    if form.validate_on_submit():

        sample = (
            db.session.query(Sample)
            .filter(Sample.id == form.samples.data)
            .first_or_404()
        )

        sample_shelf_binds = (
            db.session.query(SampleToFixedColdStorageShelf)
            .filter(SampleToFixedColdStorageShelf.sample_id == sample.id)
            .all()
        )

        sample_box_binds = (
            db.session.query(SampleToCryovialBox)
            .filter(SampleToCryovialBox.sample_id == sample.id)
            .all()
        )

        for bind in sample_shelf_binds + sample_box_binds:
            db.session.delete(bind)

        sfcs = SampleToFixedColdStorageShelf(
            sample_id=sample.id, shelf_id=shelf.id, author_id=current_user.id
        )

        db.session.add(sfcs)
        db.session.commit()

        return redirect(url_for("storage.view_shelf", id=shelf.id))

    return render_template("storage/shelf/sample_to_shelf.html", form=form, shelf=shelf)
