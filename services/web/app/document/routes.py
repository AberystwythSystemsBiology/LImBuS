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
    render_template,
    url_for,
    abort,
    current_app,
    send_file,
    session,
    flash,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

import random
import string
import os

from . import document
from .models import Document, DocumentFile
from .forms import (
    DocumentCreationForm,
    DocumentLockForm,
    PatientConsentFormInformationForm,
    DocumentUploadFileForm,
)

from ..auth.models import UserAccount
from ..misc import get_internal_api_header

from .. import db
import requests


@login_required
@document.route("/")
def index():
    response = requests.get(
        url_for("api.document_home", _external=True), headers=get_internal_api_header()
    )

    if response.status_code == 200:
        return render_template("document/index.html", documents=response.json()["content"])
    else:
        return response.content


@document.route("/new", methods=["GET", "POST"])
@login_required
def new_document():
    form = DocumentCreationForm()
    if form.validate_on_submit():

        document_information = {
            "name": form.name.data,
            "description": form.description.data,
            "type": form.type.data,
        }

        response = requests.post(
            url_for("api.document_new_document", _external=True), headers=get_internal_api_header(), json=document_information
        )

        if response.status_code == 200:
            flash("Document Successfully Created")
            return redirect(url_for("document.index"))
        else:
            return abort(response.status_code)

    return render_template("document/upload/index.html", form=form)



def save_document(file, name, description, type, uploader, commit=False) -> int:
    filename = file.data.filename
    folder_name = "".join(random.choice(string.ascii_lowercase) for _ in range(20))
    document_dir = current_app.config["DOCUMENT_DIRECTORY"]
    rel_path = os.path.join(document_dir, folder_name)
    os.makedirs(rel_path)
    sfn = secure_filename(filename)
    filepath = os.path.join(rel_path, sfn)

    document = Document(
        name=name, description=description, type=type, uploader=uploader
    )

    db.session.add(document)
    db.session.flush()

    document_file = DocumentFile(
        filename=sfn,
        filepath=filepath,
        uploader=current_user.id,
        document_id=document.id,
    )

    file.data.save(filepath)
    db.session.add(document_file)

    if commit:
        db.session.commit()

    return document.id


@document.route("/upload/file/<hash>", methods=["GET", "POST"])
@login_required
def document_upload(hash):
    form = DocumentUploadFileForm()

    if form.validate_on_submit():
        document_info = session["%s document_info" % (hash)]
        document_id = save_document(
            form.file,
            document_info["name"],
            document_info["description"],
            document_info["type"],
            current_user.id,
        )

        db.session.commit()

        return redirect(url_for("document.index"))

    return render_template("document/upload/upload.html", form=form, hash=hash)


@document.route("/LIMBDOC-<id>")
@login_required
def view(id):
    #  view = document_schema
    response = requests.get(
        url_for("api.document_view_document", id=id, _external=True), headers=get_internal_api_header()
    )
    if response.status_code == 200:
        form = DocumentLockForm(id)
        return render_template("document/view.html", document=response.json()["content"], form=form)
    else:
        return  abort(response.status_code)


@document.route("/LIMBDOC-<id>/lock", methods=["POST"])
@login_required
def lock(id):
    form = DocumentLockForm(id)

    if form.validate_on_submit():

        response = requests.get(
            url_for("api.document_view_document", id=id, _external=True), headers=get_internal_api_header()
        )
        if response.status_code == 200:
            lock_response = requests.put(
                url_for("api.document_lock_document", id=id, _external=True), headers=get_internal_api_header()
            )

            if lock_response.status_code == 200:
                flash("Document Successfully Locked")
            else:
                flash("We have a problem: %s" % (lock_reponse.json()))
            return redirect(url_for("document.view", id=id))

    else:
        return redirect(url_for("document.view", id=id))

@document.route("/LIMBDOC-<id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    response = requests.get(
        url_for("api.document_view_document", id=id, _external=True), headers=get_internal_api_header()
    )
    if response.status_code == 200:
        form = DocumentCreationForm(data=response.json()["content"])

        if form.validate_on_submit():
            form_information = {
                "name": form.name.data,
                "type": form.type.data,
                "description": form.description.data
            }

            edit_response = requests.put(
                url_for("api.document_edit_document", id=id, _external=True), headers=get_internal_api_header(), json=form_information
            )

            if edit_response.status_code == 200:
                flash("Document Successfully Edited")
            else:
                flash("We have a problem: %s" % (edit_response.json()))
            return redirect(url_for("document.view", id=id))
        return render_template("document/edit.html", document=response.json()["content"], form=form)
    else:
        return  abort(response.status_code)

@document.route("/download/D<doc_id>F<file_id>")
@login_required
def get_file(doc_id, file_id):
    file = DocumentFile.query.filter(DocumentFile.id == file_id).first()
    if current_user.is_admin or file.uploader == current_user.id:
        return send_file(file.filepath)
    else:
        return abort(401)
