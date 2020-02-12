from flask import redirect, render_template, url_for, abort, current_app, send_file, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..misc.generators import generate_random_hash


import random
import string
import os

from . import document
from .models import Document, DocumentFile, PatientConsentForm, DocumentType
from .forms import DocumentUploadForm, PatientConsentFormInformationForm, DocumentUploadFileForm

from ..sample.models import SampleDocumentAssociation

from ..auth.models import User

from .. import db

@login_required
@document.route("/")
def index():
    if current_user.is_admin:

        documents = db.session.query(
            User,
            Document
        ).filter(
            Document.uploader == User.id
        ).all()

    else:
        documents = Document.query.filter(Document.uploader == current_user.id).all()

    return render_template("document/index.html", documents=documents)

@document.route("/upload", methods=["GET", "POST"])
def upload():
    form = DocumentUploadForm()
    if form.validate_on_submit():
        document_upload_hash = generate_random_hash()

        session["%s document_info" % (document_upload_hash)] = {
            "name": form.name.data,
            "description": form.description.data,
            "type": form.type.data
        }



        '''
        
        f = form.file.data.filename

        folder_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(20))

        document_dir = current_app.config["DOCUMENT_DIRECTORY"]

        rel_path = os.path.join(document_dir, folder_name)
        os.makedirs(rel_path)

        sfn = secure_filename(f)

        filepath = os.path.join(rel_path, sfn)

        document = Document(
            name = form.name.data,
            description = form.description.data,
            type = form.type.data,
            uploader = current_user.id,
        )

        db.session.add(document)

        db.session.flush()

        document_file = DocumentFile(
            filename = sfn,
            filepath = filepath,
            uploader=current_user.id,
            document_id=document.id
        )

        form.file.data.save(filepath)

        db.session.add(document_file)
        db.session.commit()
        '''

        if form.type.data == "PATIE":
            return redirect(url_for("document.patient_consent_form_settings", hash=document_upload_hash))
        return redirect(url_for("document.document_upload", hash=hash))


    return render_template("document/upload/index.html", form=form)

@document.route("/upload/pcf/<hash>", methods=["GET", "POST"])
def patient_consent_form_settings(hash):
    form = PatientConsentFormInformationForm()

    if form.validate_on_submit():
        session["%s patient_consent_info" % (hash)] = {
            "academic": form.academic.data,
            "commercial": form.commercial.data,
            "animal": form.animal.data,
            "genetic": form.genetic.data
        }

        return redirect(url_for("document.document_upload", hash=hash))

    return render_template("document/upload/patient_consent.html", form=form, hash=hash)

@document.route("/upload/file/<hash>", methods=["GET", "POST"])
def document_upload(hash):
    form = DocumentUploadFileForm()

    if form.validate_on_submit():

        pass

    return render_template("document/upload/upload.html", form=form, hash=hash)


@document.route("/view/LIMBDOC-<doc_id>")
def view(doc_id):

    upload_user, document = db.session.query(
        User, Document
    ).filter(Document.id == doc_id).filter(DocumentFile.uploader == User.id).first()

    if current_user.is_admin or upload_user.id == current_user.id:

        files = db.session.query(
            User,
            DocumentFile
        ).filter(DocumentFile.uploader == User.id).filter(DocumentFile.document_id == doc_id).all()

        # TODO: Build an association view class
        associated_document = db.session.query(SampleDocumentAssociation).filter(SampleDocumentAssociation.document_id == doc_id).all()

        return render_template("document/view.html", document=document, upload_user=upload_user, files=files, associated_document=associated_document)

    else:
        return abort(401)

@document.route("/download/D<doc_id>F<file_id>")
def get_file(doc_id, file_id):
    file = DocumentFile.query.filter(DocumentFile.id == file_id).first()
    if current_user.is_admin or file.uploader == current_user.id:
        return send_file(file.filepath)
    else:
        return abort(401)