# Copyright (C) 2019  Keiron O'Shea <keo7@aber.ac.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

from .. import storage
import requests
from ...misc import get_internal_api_header
from flask_login import current_user, login_required

from ..forms import (
    ColdStorageForm,
    NewShelfForm,
    ColdStorageServiceReportForm,
    ColdStorageToDocumentAssociationForm,
)


@storage.route("/coldstorage/new/LIMROOM-<id>", methods=["GET", "POST"])
@login_required
def new_cold_storage(id):

    response = requests.get(
        url_for("api.storage_room_view", id=id, _external=True),
        headers=get_internal_api_header(),
    )

    if response.status_code == 200:
        form = ColdStorageForm()

        if form.validate_on_submit():
            new_response = requests.post(
                url_for("api.storage_coldstorage_new", _external=True),
                headers=get_internal_api_header(),
                json={
                    "alias": form.alias.data,
                    "room_id": id,
                    "status": form.status.data,
                    "serial_number": form.serial_number.data,
                    "manufacturer": form.manufacturer.data,
                    "comments": form.comments.data,
                    "temp": form.temperature.data,
                    "type": form.type.data,
                },
            )

            if new_response.status_code == 200:
                flash("Cold Storage Successfuly Created")
                return redirect(
                    url_for(
                        "storage.view_cold_storage",
                        id=new_response.json()["content"]["id"],
                    )
                )
            else:
                flash("We have a problem", new_response.json())

        return render_template(
            "storage/lts/new.html", form=form, room=response.json()["content"]
        )

    else:
        abort(response.status_code)


@storage.route("/coldstorage/LIMBCS-<id>/new/report", methods=["GET", "POST"])
@login_required
def new_cold_storage_servicing_report(id: int):
    response = requests.get(
        url_for("api.storage_coldstorage_view", id=id, _external=True),
        headers=get_internal_api_header(),
    )

    if response.status_code == 200:
        form = ColdStorageServiceReportForm()

        if form.validate_on_submit():

            new_response = requests.post(
                url_for(
                    "api.storage_coldstorage_new_service_report", id=id, _external=True
                ),
                headers=get_internal_api_header(),
                json={
                    "date": str(form.date.data),
                    "conducted_by": form.conducted_by.data,
                    "temp": float(form.temp.data),
                    "status": form.status.data,
                    "comments": form.comments.data,
                },
            )

            if new_response.status_code == 200:
                flash("Service Report Added")
                return redirect(url_for("storage.view_cold_storage", id=id))
            else:
                flash("We have a problem: %s" % (new_response.json()))
        return render_template(
            "storage/lts/servicing/new.html", form=form, cs=response.json()["content"]
        )

    abort(response.status_code)


@storage.route("/coldstorage/LIMBCS-<id>/associate/document", methods=["GET", "POST"])
@login_required
def associate_document(id):
    response = requests.get(
        url_for("api.storage_coldstorage_view", id=id, _external=True),
        headers=get_internal_api_header(),
    )

    if response.status_code == 200:

        document_response = requests.get(
            url_for("api.document_home", _external=True),
            headers=get_internal_api_header(),
        )

        if document_response.status_code == 200:

            documents = []

            for document in document_response.json()["content"]:
                documents.append(
                    [
                        int(document["id"]),
                        "LIMBDOC-%s: %s" % (document["id"], document["name"]),
                    ]
                )

            form = ColdStorageToDocumentAssociationForm(documents)

            if form.validate_on_submit():

                new_document_association_response = requests.post(
                    url_for("api.storage_coldstorage_document", id=id, _external=True),
                    headers=get_internal_api_header(),
                    json={
                        "document_id": form.document_id.data
                    }
                )

                if new_document_association_response.status_code == 200:
                    flash("Document Associated")
                    return redirect(url_for("storage.view_cold_storage", id=id))
                else:
                    flash("We have a problem:", new_document_association_response.json())
            return render_template(
                "storage/lts/associate/document.html",
                cs=response.json()["content"],
                form=form,
            )
    return abort(response.status_code)


@storage.route("/coldstorage/LIMBCS-<id>", methods=["GET"])
@login_required
def view_cold_storage(id):
    response = requests.get(
        url_for("api.storage_coldstorage_view", id=id, _external=True),
        headers=get_internal_api_header(),
    )

    if response.status_code == 200:
        return render_template("storage/lts/view.html", cs=response.json()["content"])
    return abort(response.status_code)


@storage.route("/coldstorage/LIMBCS-<id>/edit", methods=["GET", "POST"])
@login_required
def edit_cold_storage(id):
    response = requests.get(
        url_for("api.storage_coldstorage_view", id=id, _external=True),
        headers=get_internal_api_header(),
    )

    if response.status_code == 200:
        form = ColdStorageForm(data=response.json()["content"])
        if form.validate_on_submit():
            form_information = {
                "alias": form.alias.data,
                "serial_number": form.serial_number.data,
                "manufacturer": form.manufacturer.data,
                "comments": form.comments.data,
                "temp": form.temperature.data,
                "type": form.type.data,
            }

            edit_response = requests.put(
                url_for("api.storage_coldstorage_edit", id=id, _external=True),
                headers=get_internal_api_header(),
                json=form_information,
            )

            if edit_response.status_code == 200:
                flash("Cold Storage Successfully Edited")
            else:
                flash("We have a problem: %s" % (edit_response.json()))

            return redirect(url_for("storage.view_cold_storage", id=id))
        return render_template(
            "storage/lts/edit.html", cs=response.json()["content"], form=form
        )

    return abort(response.status_code)
