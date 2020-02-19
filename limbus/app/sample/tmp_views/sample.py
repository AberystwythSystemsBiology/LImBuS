from flask import render_template, redirect, session, url_for

from .. import sample
from flask_login import login_required
from ... import db

from ..models import *

from ...auth.models import User

from ..forms import SampleAttributeCreationForm, SampleCreationForm, DynamicAttributeSelectForm, p, SampleAttributionCreationFormText, PatientConsentFormSelectForm

from ...dynform import DynamicAttributeFormGenerator, clear_session

from ...misc.generators import generate_random_hash


@sample.route("view/LIMBSMP-<sample_id>")
@login_required
def view(sample_id):
    sample = db.session.query(Sample).filter(Sample.id == sample_id).first()
    text_attr = db.session.query(
        SampleAttribute,
        SampleAttributeTextValue
    ).filter(
        SampleAttributeTextValue.sample_id == sample_id
    ).filter(
        SampleAttributeTextValue.sample_attribute_id == SampleAttribute.id
    ).all()

    option_attr = db.session.query(
        SampleAttribute,
        SampleAttributeOptionValue,
        SampleAttributeOption
    ).filter(
        SampleAttributeOptionValue.sample_id == sample_id
    ).filter (
        SampleAttributeOptionValue.sample_attribute_id == SampleAttribute.id
    ).filter(
        SampleAttributeOptionValue.sample_option_id == SampleAttributeOption.id
    ).all()

    associated_document = db.session.query(
        SampleDocumentAssociation, Document
    ).filter(SampleDocumentAssociation.sample_id == sample_id).filter(SampleDocumentAssociation.document_id == Document.id).all()

    return render_template("sample/information/view.html", sample=sample, text_attr=text_attr, option_attr=option_attr, associated_document=associated_document)

'''
    Add New Sample:
    
    The following code relates to the addition of new samples. 
'''

@sample.route("add/step_zero", methods=["GET", "POST"])
@login_required
def add_sample_pcf():
    document_selection, pcf_documents = PatientConsentFormSelectForm()

    if document_selection.validate_on_submit():
        sample_add_hash = generate_random_hash()
        session["%s consent_id" % (sample_add_hash)] = document_selection.form_select.data

        return redirect(url_for('sample.add_sample_attr', hash=sample_add_hash))
    return render_template("sample/information/select_document.html", form=document_selection, pcf_documents=pcf_documents)

@sample.route("add/step_one/<hash>", methods=["GET", "POST"])
@login_required
def add_sample_attr(hash):

    query = db.session.query(SampleAttribute).all()
    conv = {p.number_to_words(x.id) : x.id for x in query}
    attr_selection = DynamicAttributeSelectForm(query, "term")

    if attr_selection.validate_on_submit():
        attribute_ids = []
        for attr in attr_selection:
            if attr.id in conv and attr.data == True:
                attribute_ids.append(conv[attr.id])

        session["%s sample_attributes" % (hash)] = attribute_ids
        session["%s converted_ids" % (hash)] = conv

        return redirect(url_for('sample.add_sample_form', hash=hash))
    return render_template("sample/information/select_attributes.html", form=attr_selection, hash=hash)



@sample.route("add/step_two/<hash>", methods=["GET", "POST"])
@login_required
def add_sample_form(hash):
    query = db.session.query(SampleAttribute).filter(SampleAttribute.id.in_(session["%s sample_attributes" % (hash)])).all()
    form = DynamicAttributeFormGenerator(query, SampleCreationForm).make_form()

    if form.validate_on_submit():
        sample = Sample(
            sample_type=form.sample_type.data,
            collection_date=form.collection_date.data,
            disposal_instruction=form.disposal_instruction.data,
            disposal_date = form.disposal_date.data,
            author_id=current_user.id,
            sample_status=form.sample_status.data,
            batch_number = form.batch_number.data
        )

        db.session.add(sample)
        db.session.flush()

        # TODO: Add attribute to form element to differ between classes.

        for attr in form:
            if attr.id not in ["csrf_token", "biobank_accession_number", "sample_status", "batch_number", "submit", "sample_type", "collection_date", "disposal_instruction"]:
                if attr.type in ["TextAreaField", "StringField"]:
                    attr_value = SampleAttributeTextValue(
                        value = attr.data,
                        sample_attribute_id = session["%s converted_ids" % (hash)][attr.id],
                        sample_id = sample.id,
                        author_id = current_user.id
                    )
                    db.session.add(attr_value)

                elif attr.type in ["SelectField"]:
                    option = db.session.query(SampleAttributeOption).filter(SampleAttributeOption.term == attr.data).first()

                    option_value = SampleAttributeOptionValue(
                        sample_attribute_id=session["%s converted_ids" % (hash)][attr.id],
                        sample_id=sample.id,
                        sample_option_id=option.id,
                        author_id = current_user.id
                    )

                    db.session.add(option_value)

        sda = SampleDocumentAssociation(
            sample_id = sample.id,
            document_id = session["%s consent_id" % (hash)],
            author_id = current_user.id
        )

        db.session.add(sda)
        db.session.commit()

        clear_session(hash)

        return redirect(url_for("sample.index"))

    return render_template("sample/information/add.html", form=form, hash=hash)