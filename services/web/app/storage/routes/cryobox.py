from flask import (
    redirect,
    abort,
    render_template,
    url_for,
    session,
    request,
    jsonify,
    Response,
    flash,
)
from flask_login import current_user, login_required

from ... import db
from .. import storage

from ...misc.generators import generate_random_hash
from .misc import move_entity_to_storage
from ..enums import EntityToStorageTpye

from ..views import CryoboxIndexView, CryoboxView

from ...auth.views import UserView

from ..models import CryovialBox, EntityToStorage

from ..forms import (
    NewCryovialBoxForm,
    SampleToEntityForm,
    NewCryovialBoxFileUploadForm,
    CryoBoxFileUploadSelectForm,
)

from ...auth.models import User
from ...sample.models import Sample
from string import ascii_uppercase
import itertools
import re

from ...misc import clear_session


def iter_all_strings():
    for size in itertools.count(1):
        for s in itertools.product(ascii_uppercase, repeat=size):
            yield "".join(s)


values = []
for i in iter_all_strings():
    values.append(i)
    if i == "ZZZ":
        break


def file_to_json(form) -> dict:
    data = {}

    csv_data = [
        x.decode("UTF-8").replace("\n", "").split(",") for x in form.file.data.stream
    ]

    # Get Indexes
    indexes = {
        "Tube Barcode": csv_data[0].index("Tube Barcode"),
        "Tube Position": csv_data[0].index("Tube Position"),
        "Tube Row": [],
        "Tube Column": [],
    }

    positions = {
        x[indexes["Tube Position"]]: x[indexes["Tube Barcode"]] for x in csv_data[1:]
    }

    data["positions"] = positions

    # Going to use plain old regex to do the splits
    regex = re.compile(r"(\d+|\s+)")

    for position in data["positions"].keys():
        splitted = regex.split(position)
        indexes["Tube Column"].append(splitted[0])
        indexes["Tube Row"].append(int(splitted[1]))

    data["num_cols"] = len(list(set(indexes["Tube Column"])))
    data["num_rows"] = max(indexes["Tube Row"])
    data["serial_number"] = form.serial.data

    return data


@storage.route("/cryobox")
@login_required
def cryobox_index():
    boxes = CryoboxIndexView()
    return render_template("storage/cryobox/index.html", boxes=boxes)


@storage.route("/cryobox/new", methods=["GET", "POST"])
@login_required
def add_cryobox():
    return render_template("storage/cryobox/new/option.html")


@storage.route("/cryobox/new/manual", methods=["GET", "POST"])
@login_required
def cryobox_manual_entry():
    form = NewCryovialBoxForm()
    if form.validate_on_submit():
        cb = CryovialBox(
            serial=form.serial.data,
            num_rows=form.num_rows.data,
            num_cols=form.num_cols.data,
            removed=False,
            author_id=current_user.id,
        )

        db.session.add(cb)
        db.session.commit()

        flash("Cryovial Box Added")
        return redirect(url_for("storage.cryobox_index"))

    return render_template("storage/cryobox/new/manual/new.html", form=form)


@storage.route("/cryobox/new/from_file", methods=["GET", "POST"])
@login_required
def cryobox_from_file():
    form = NewCryovialBoxFileUploadForm()
    if form.validate_on_submit():
        hash = generate_random_hash()
        session[hash] = file_to_json(form)
        return redirect(url_for("storage.crybox_from_file_validation", hash=hash))
    return render_template("storage/cryobox/new/from_file/step_one.html", form=form)


@storage.route("/cryobox/new/from_file/validation/<hash>", methods=["GET", "POST"])
@login_required
def crybox_from_file_validation(hash: str):
    session_data = session[hash]

    sample_data = {}

    for position, barcode in session_data["positions"].items():
        sample_data[position] = {
            "barcode": barcode,
            "sample": db.session.query(Sample)
            .filter(Sample.biobank_barcode == barcode)
            .first(),
        }

    form = CryoBoxFileUploadSelectForm(sample_data)

    if form.validate_on_submit():

        cry = CryovialBox(
            serial=session_data["serial_number"],
            num_rows=session_data["num_rows"],
            num_cols=session_data["num_cols"],
            author_id=current_user.id,
        )

        db.session.add(cry)
        db.session.flush()

        for ele in form:
            if ele.type == "BooleanField":
                if ele.data:
                    regex = re.compile(r"(\d+|\s+)")
                    col, row, _ = regex.split(ele.id)
                    sample_id = ele.render_kw["_sample"].id

        db.session.commit()
        clear_session(hash)
        return redirect(url_for("storage.cryobox_index"))
    return render_template(
        "storage/cryobox/new/from_file/step_two.html",
        form=form,
        hash=hash,
        session_data=session_data,
    )


@storage.route("/cryobox/view/LIMBCRB-<cryo_id>")
@login_required
def view_cryobox(cryo_id):
    cryo = CryoboxView(cryo_id)
    return render_template("storage/cryobox/view.html", cryo=cryo)


from sqlalchemy_continuum import version_class
from sqlalchemy import desc


@storage.route("/cryobox/view/LIMB<storage_type>-<id>/history")
@login_required
def view_history(storage_type, id):
    EntityToStorageVersioned = version_class(EntityToStorage)
    if storage_type == "CRB":
        attr = "box_id"

    changes = {}

    for change in (
        db.session.query(EntityToStorageVersioned)
        .filter(getattr(EntityToStorageVersioned, attr) == id)
        .order_by(desc(EntityToStorageVersioned.update_date))
        .all()
    ):
        changes[change.id] = {
            "sample_id": change.sample_id,
            "box_id": change.box_id,
            "shelf_id": change.shelf_id,
            "storage_type": change.storage_type.value,
            "row": change.row,
            "col": change.col,
            "entered_by": change.entered_by,
            "entered": change.entered,
            "update_date": change.update_date,
            "author_information": UserView(change.author_id)
        }

    return render_template("storage/history.html", storage_type=storage_type, id=id, changes=changes)


@storage.route(
    "cryobox/add/sample/LIMCRB-<cryo_id>/<row>_<col>", methods=["GET", "POST"]
)
@login_required
def add_cryobox_sample(cryo_id, row, col):
    cryo = (
        db.session.query(CryovialBox).filter(CryovialBox.id == cryo_id).first_or_404()
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
            sample_id=sample.id,
            box_id=cryo_id,
            row=row,
            col=col,
            entered=form.date.data.strftime("%Y-%m-%d, %H:%M:%S"),
            entered_by=form.entered_by.data,
            author_id=current_user.id,
            storage_type=EntityToStorageTpye.STB,
        )

        flash("Sample assigned to shelf!")
        return redirect(url_for("storage.view_cryobox", cryo_id=cryo_id))

    return render_template(
        "storage/cryobox/sample_to_box.html", cryo=cryo, form=form, row=row, col=col
    )
