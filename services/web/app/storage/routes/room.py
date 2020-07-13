from flask import redirect, abort, render_template, url_for, session, request, jsonify

from flask_login import current_user, login_required
from ... import db
from .. import storage

from ..forms import SiteRegistrationForm, RoomRegistrationForm, LongTermColdStorageForm

from ..models import (
    Site,
    Room,
    FixedColdStorage,
    FixedColdStorageShelf,
)

from ...misc.models import Address
from ...auth.models import User


@storage.route("rooms/")
@login_required
def room_index():
    sites = db.session.query(Site, User).filter(Site.author_id == User.id).all()
    return render_template("storage/site/index.html", sites=sites)


@storage.route("rooms/new", methods=["GET", "POST"])
@login_required
def add_room():
    form = SiteRegistrationForm()
    if form.validate_on_submit():

        addr = Address(
            street_address_one=form.address_line_one.data,
            street_address_two=form.address_line_two.data,
            city=form.city.data,
            county=form.county.data,
            post_code=form.post_code.data,
            country=form.country.data,
        )

        db.session.add(addr)

        db.session.flush()

        site = Site(name=form.name.data, address_id=addr.id, author_id=current_user.id)

        db.session.add(site)
        db.session.commit()

        return redirect(url_for("storage.site_index"))

    return render_template("storage/site/new.html", form=form)


@storage.route("/rooms/view/LIMBROM-<id>")
@login_required
def view_room(id):
    site = db.session.query(Site).filter(Site.id == Room.site_id).first_or_404()
    room = db.session.query(Room).filter(Room.id == id).first_or_404()
    ltss = (
        db.session.query(FixedColdStorage).filter(FixedColdStorage.room_id == id).all()
    )

    return render_template("storage/room/view.html", site=site, room=room, ltss=ltss)


@storage.route("/rooms/view/LIMBROM-<id>/get")
@login_required
def get_room(id):
    site = db.session.query(Site).filter(Site.id == id).first_or_404()
    rooms = db.session.query(Room).filter(Room.site_id == Site.id).all()

    output = {}

    for room in rooms:
        output[room.id] = {
            "name": room.room_number,
            "building": room.building,
            "storage": {},
        }
        fixed_storage = (
            db.session.query(FixedColdStorage)
            .filter(FixedColdStorage.room_id == room.id)
            .all()
        )
        for storage in fixed_storage:

            output[room.id]["storage"][storage.id] = {
                "serial_number": storage.serial_number,
                "manufacturer": storage.manufacturer,
                "temperature": storage.temperature.value,
                "type": storage.type.value,
                "shelves": {},
            }

            shelves = (
                db.session.query(FixedColdStorageShelf)
                .filter(FixedColdStorageShelf.storage_id == storage.id)
                .all()
            )

            for shelf in shelves:
                output[room.id]["storage"][storage.id]["shelves"][shelf.id] = {
                    "name": shelf.name,
                    "samples": {},
                    "cryo": {},
                }
                """'
                samples_to_shelf = (
                    db.session.query(SampleToFixedColdStorageShelf)
                    .filter(SampleToFixedColdStorageShelf.shelf_id == shelf.id)
                    .all()
                )

                for sample in samples_to_shelf:
                    output[room.id]["storage"][storage.id]["shelves"][shelf.id][
                        "samples"
                    ][sample.id] = {"type": sample.sample_type}

                cryo_to_shelf = (
                    db.session.query(CryovialBoxToFixedColdStorageShelf)
                    .filter(CryovialBoxToFixedColdStorageShelf.shelf_id == shelf.id)
                    .all()
                )

                for cryo in cryo_to_shelf:

                    output[room.id]["storage"][storage.id]["shelves"][shelf.id]["cryo"][
                        cryo.id
                    ] = {"test": "data"}
                """

    return jsonify(output), 201, {"Content-Type": "application/json"}


@storage.route("/rooms/add_lts/LIMBROM-<id>", methods=["GET", "POST"])
@login_required
def add_lts(id):
    room = db.session.query(Room).filter(Room.id == id).first_or_404()
    form = LongTermColdStorageForm()

    if form.validate_on_submit():
        fcs = FixedColdStorage(
            serial_number=form.serial_number.data,
            manufacturer=form.manufacturer.data,
            temperature=form.temperature.data,
            type=form.type.data,
            room_id=id,
            author_id=current_user.id,
        )

        db.session.add(fcs)
        db.session.commit()
        return redirect(url_for("storage.view_room", id=id))

    return render_template("storage/lts/new.html", form=form, room=room)
