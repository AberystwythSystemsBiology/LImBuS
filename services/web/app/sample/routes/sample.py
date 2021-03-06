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

from .. import sample
import requests
from flask import render_template, url_for, flash, redirect, abort
from flask_login import login_required

import requests
from ...misc import get_internal_api_header

from ..forms import (
    SampleToDocumentAssociatationForm,
    SampleReviewForm,
    ProtocolEventForm,
)

from datetime import datetime


@sample.route("<uuid>", methods=["GET"])
@login_required
def view(uuid: str):
    return render_template("sample/view.html", uuid=uuid)


@sample.route("<uuid>/associate/document", methods=["GET", "POST"])
@login_required
def associate_document(uuid):

    sample_response = requests.get(
        url_for("api.sample_view_sample", uuid=uuid, _external=True),
        headers=get_internal_api_header(),
    )

    if sample_response.status_code == 200:
        document_response = requests.get(
            url_for("api.document_home", _external=True),
            headers=get_internal_api_header(),
        )

        if document_response.status_code == 200:

            form = SampleToDocumentAssociatationForm(
                document_response.json()["content"]
            )

            if form.validate_on_submit():

                response = requests.post(
                    url_for("api.sample_to_document", _external=True),
                    headers=get_internal_api_header(),
                    json={
                        "sample_id": sample_response.json()["content"]["id"],
                        "document_id": form.documents.data,
                    },
                )

                if response.status_code == 200:
                    flash("Document successfully associated")
                else:
                    flash("We have a problem :( %s" % (response.json()))

                return redirect(url_for("sample.view", uuid=uuid))

            return render_template(
                "sample/associate/document.html",
                sample=sample_response.json()["content"],
                form=form,
            )

        return abort(document_response.status_code)

    return abort(sample_response.status_code)


@sample.route("<uuid>/data", methods=["GET"])
@login_required
def view_data(uuid: str):
    sample_response = requests.get(
        url_for("api.sample_view_sample", uuid=uuid, _external=True),
        headers=get_internal_api_header(),
    )

    if sample_response.status_code == 200:
        return sample_response.json()
    return sample_response.content
