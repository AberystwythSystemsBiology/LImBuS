from flask import redirect, abort, render_template, url_for, session, request, jsonify
from flask_login import current_user, login_required

from .. import processing

from ..forms import NewProtocolForm

from ... import db
from ...auth.models import User

from ..models import *
from ...document.models import Document
from ...document.routes import save_document
from ...document.models import DocumentType

from ..views import ProcessingProtocolsIndexView, ProcessingProtocolView


@processing.route("/protocols")
@login_required
def protocol_index():
    protocols = ProcessingProtocolsIndexView()
    return render_template("processing/protocols/index.html", protocols=protocols)


@processing.route("/protocols/new", methods=["GET", "POST"])
@login_required
def new_protocol():
    form = NewProtocolForm()
    if form.validate_on_submit():
        has_document = bool(form.document_upload.data)

        pt = ProcessingTemplate(
            name=form.name.data,
            type=form.protocol_type.data,
            sample_type=form.sample_type.data,
            has_document=has_document,
            author_id=current_user.id,
        )

        db.session.add(pt)
        db.session.flush()

        if has_document:
            doc_id = save_document(
                form.document_upload,
                "%s Document" % form.name.data,
                "",
                DocumentType.PROTO,
                current_user.id,
            )

            pttd = ProcessingTemplateToDocument(
                template_id=pt.id, document_id=doc_id, author_id=current_user.id
            )

            db.session.add(pttd)
            db.session.flush()

        db.session.commit()

        return redirect(url_for("processing.protocol_index"))
    return render_template("processing/protocols/new/one.html", form=form)


@processing.route("/protocols/view/LIMBPRO-<protocol_id>")
@login_required
def view_protocol(protocol_id):
    protocol = ProcessingProtocolView(protocol_id)

    return render_template("processing/protocols/view.html", protocol=protocol)
