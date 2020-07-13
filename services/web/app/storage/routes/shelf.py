from flask import (
    redirect,
    abort,
    render_template,
    url_for,
    session,
    request,
    jsonify,
    flash,
)
from flask_login import current_user, login_required

from ... import db
from .. import storage

from .misc import move_entity_to_storage


from ..models import (
    FixedColdStorageShelf,
    CryovialBox,
)
from ...sample.models import Sample

from ..forms import SampleToEntityForm, BoxToShelfForm
from ..views import ShelfView
from ...misc import chunks
from ..enums import EntityToStorageTpye


@storage.route("/shelves/view/LIMBSHF-<id>")
@login_required
def view_shelf(id):
    shelf = ShelfView(id)
    # Conversion to make it renderable in a nice way.
    shelf["cryoboxes"] = chunks([x for x in shelf["cryoboxes"].items()], 4)
    return render_template("storage/shelf/view.html", shelf=shelf)


@storage.route("/shelves/LIMBSHF-<shelf_id>/assign_box", methods=["GET", "POST"])
@login_required
def assign_box_to_shelf(shelf_id):
    shelf = ShelfView(shelf_id)

    form = BoxToShelfForm(db.session.query(CryovialBox).all())

    if form.validate_on_submit():
        move_entity_to_storage(
            box_id = form.boxes.data,
            shelf_id=shelf_id,
            entered=form.date.data.strftime('%Y-%m-%d, %H:%M:%S'),
            entered_by=form.entered_by.data,
            author_id=current_user.id,
            storage_type=EntityToStorageTpye.BTS
        )

        flash("LIMBCRB-%i successfully moved!" % (form.boxes.data))
        return redirect(url_for("storage.view_shelf", id=shelf_id))

    return render_template("/storage/shelf/box_to_shelf.html", shelf=shelf, form=form)


@storage.route("/shelves/LIMBSHF-<shelf_id>/assign_sample", methods=["GET", "POST"])
@login_required
def assign_sample_to_shelf(shelf_id):
    shelf = (
        db.session.query(FixedColdStorageShelf)
        .filter(FixedColdStorageShelf.id == shelf_id)
        .first_or_404()
    )
    samples = db.session.query(Sample).all()

    form = SampleToEntityForm(samples)

    if form.validate_on_submit():

        sample = (
            db.session.query(Sample)
            .filter(Sample.id == form.samples.data)
            .first_or_404()
        )

        move_entity_to_storage(
            sample_id = sample.id,
            shelf_id=shelf_id,
            entered=form.date.data.strftime('%Y-%m-%d, %H:%M:%S'),
            entered_by=form.entered_by.data,
            author_id=current_user.id,
            storage_type=EntityToStorageTpye.STS
        )

        flash("Sample assigned to shelf!")

        return redirect(url_for("storage.view_shelf", id=shelf.id))

    return render_template("storage/shelf/sample_to_shelf.html", form=form, shelf=shelf)
