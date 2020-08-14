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

from flask import render_template, redirect, session, url_for, flash, abort
from flask_login import login_required, current_user

from ...misc import get_internal_api_header

from .. import sample

from ..forms import (
    CollectionConsentAndDisposalForm,
    PatientConsentQuestionnaire,
    SampleTypeSelectForm,
    ProtocolTemplateSelectForm,
    SampleReviewForm,
    CustomAttributeSelectForm
)

import requests

@sample.route("add/reroute/<hash>", methods=["GET"])
@login_required
def add_rerouter(hash):
    if hash == "new":
        return redirect(url_for("sample.add_collection_consent_and_barcode"))

    query_response = requests.get(
        url_for("api.tmpstore_view_tmpstore", hash=hash, _external=True),
        headers=get_internal_api_header(),
    )

    if query_response.status_code == 200:
        data = query_response.json()["content"]["data"]

    if "add_collection_consent_and_barcode" not in data:
        return redirect(url_for("sample.add_collection_consent_and_barcode"))
    else:
        if "add_digital_consent_form" in data:
            if "add_sample_information" in data:
                if "add_processing_information" in data:
                    if "add_sample_review" in data:
                        return redirect(url_for("sample.add_custom_atributes", hash=hash))
                    return redirect(url_for("sample.add_sample_review", hash=hash))
                return redirect(url_for("sample.add_processing_information", hash=hash))
            return redirect(url_for("sample.add_sample_information", hash=hash))
        return redirect(url_for("sample.add_digital_consent_form", hash=hash))


    abort(400)


@sample.route("add/", methods=["GET", "POST"])
@login_required
def add_collection_consent_and_barcode():
    consent_templates = []
    collection_protocols = []
    processing_protocols = []

    consent_templates_response = requests.get(
        url_for("api.consent_query", _external=True),
        headers= get_internal_api_header(),
        json={"is_locked": False}
    )

    if consent_templates_response.status_code == 200:
        for template in consent_templates_response.json()["content"]:
            consent_templates.append([template["id"], "LIMBPCF-%i: %s" % (template["id"], template["name"])])


    protocols_response = requests.get(
        url_for("api.protocol_query", _external=True),
        headers= get_internal_api_header(),
        json={"is_locked": False}
    )

    if protocols_response.status_code == 200:
        for protocol in protocols_response.json()["content"]:
            if protocol["type"] == "ACQ":
                collection_protocols.append([protocol["id"], "LIMBPRO-%i: %s" % (protocol["id"], protocol["name"])])
            elif protocol["type"] == "SAP":
                processing_protocols.append([protocol["id"], "LIMBPRO-%i: %s" % (protocol["id"], protocol["name"])])

    form = CollectionConsentAndDisposalForm(consent_templates, collection_protocols)

    if form.validate_on_submit():

        route_data = {
            "barcode": form.barcode.data,
            "collection_protocol_id": form.collection_select.data,
            "collected_by": form.collected_by.data,
            "consent_form_id": form.consent_select.data,
            "collection_date": str(form.collection_date.data),
            "disposal_instruction": form.disposal_instruction.data,
            "disposal_date": str(form.disposal_date.data),
            "has_donor": form.has_donor.data,
        }

        # This needs to be broken out to a new module then...
        store_response = requests.post(
            url_for("api.tmpstore_new_tmpstore", _external=True),
            headers=get_internal_api_header(),
            json={"data": {"add_collection_consent_and_barcode": route_data}, "type": "SMP"}
        )

        if store_response.status_code == 200:

            return redirect(
                url_for("sample.add_rerouter", hash=store_response.json()["content"]["uuid"])
            )

        flash("We have a problem :( %s" % (store_response.json()))

    return render_template(
        "sample/sample/add/step_one.html",
        form=form,
        template_count=len(consent_templates),
        collection_protocol_count=len(collection_protocols),
        processing_protocols_count=len(processing_protocols)
    )


@sample.route("add/digital_consent_form/<hash>", methods=["GET", "POST"])
@login_required
def add_digital_consent_form(hash):

    tmpstore_response = requests.get(
        url_for("api.tmpstore_view_tmpstore", hash=hash, _external=True),
        headers=get_internal_api_header(),
    )

    if tmpstore_response.status_code != 200:
        abort(tmpstore_response.status_code)

    tmpstore_data = tmpstore_response.json()["content"]["data"]
    consent_id = tmpstore_data["add_collection_consent_and_barcode"]["consent_form_id"]

    consent_response = requests.get(
        url_for("api.consent_view_template", id=consent_id, _external=True),
        headers=get_internal_api_header()
    )

    if consent_response.status_code != 200:
        abort(consent_response.status_code)

    consent_template = consent_response.json()["content"]

    questionnaire = PatientConsentQuestionnaire(consent_template)

    if questionnaire.validate_on_submit():
        consent_details = {
            "consent_id": questionnaire.consent_id.data,
            "comments": questionnaire.comments.data,
            "date_signed": str(questionnaire.date_signed.data),
            "checked": []
        }

        for question in consent_template["questions"]:
            if getattr(questionnaire, str(question["id"])).data:
                consent_details["checked"].append(question["id"])


        tmpstore_data["add_digital_consent_form"] = consent_details

        store_response = requests.put(
            url_for("api.tmpstore_edit_tmpstore", hash=hash, _external=True),
            headers=get_internal_api_header(),
            json={"data": tmpstore_data}
        )

        if store_response.status_code == 200:
            return redirect(
                url_for("sample.add_rerouter", hash=store_response.json()["content"]["uuid"])
            )

        flash("We have a problem :( %s" % (store_response.json()))


    return render_template(
        "sample/sample/add/step_two.html",
        hash=hash,
        consent_template=consent_template,
        questionnaire=questionnaire,
    )


@sample.route("add/sample_information/<hash>", methods=["GET", "POST"])
@login_required
def add_sample_information(hash):
    tmpstore_response = requests.get(
        url_for("api.tmpstore_view_tmpstore", hash=hash, _external=True),
        headers=get_internal_api_header(),
    )

    if tmpstore_response.status_code != 200:
        abort(tmpstore_response.status_code)

    tmpstore_data = tmpstore_response.json()["content"]["data"]

    form = SampleTypeSelectForm()

    if form.validate_on_submit():

        sample_information_details = {
            "sample_type": form.sample_type.data,
            "fluid_sample_type": form.fluid_sample_type.data,
            "molecular_sample_type": form.molecular_sample_type.data,
            "cell_sample_type": form.cell_sample_type.data,
            "quantity": form.quantity.data,
            "fixation_type": form.fixation_type.data,
            "fluid_container": form.fluid_container.data,
            "cell_container": form.cell_container.data
        }

        tmpstore_data["add_sample_information"] = sample_information_details

        store_response = requests.put(
            url_for("api.tmpstore_edit_tmpstore", hash=hash, _external=True),
            headers=get_internal_api_header(),
            json={"data": tmpstore_data}
        )

        if store_response.status_code == 200:
            return redirect(
                url_for("sample.add_rerouter", hash=store_response.json()["content"]["uuid"])
            )

        flash("We have a problem :( %s" % (store_response.json()))

    return render_template("sample/sample/add/step_three.html", form=form, hash=hash)


@sample.route("add/processing_information/<hash>", methods=["GET", "POST"])
def add_processing_information(hash):

    tmpstore_response = requests.get(
        url_for("api.tmpstore_view_tmpstore", hash=hash, _external=True),
        headers=get_internal_api_header(),
    )

    if tmpstore_response.status_code != 200:
        abort(tmpstore_response.status_code)

    tmpstore_data = tmpstore_response.json()["content"]["data"]

    protocols_response = requests.get(
        url_for("api.protocol_query", _external=True),
        headers=get_internal_api_header(),
        json={"is_locked": False, "type": "SAP"}
    )
    processing_protocols = []

    if protocols_response.status_code == 200:
        for protocol in protocols_response.json()["content"]:
            processing_protocols.append([protocol["id"], "LIMBPRO-%i: %s" % (protocol["id"], protocol["name"])])

    form = ProtocolTemplateSelectForm(processing_protocols)


    if form.validate_on_submit():
        processing_information_details = {
            "processing_protocol_id": form.processing_protocol_id.data,
            "sample_status": form.sample_status.data,
            "processing_date": str(form.processing_date.data),
            "processing_time": form.processing_time.data.strftime("%H:%M:%S"),
            "comments": form.comments.data,
            "undertaken_by": form.undertaken_by.data
        }

        tmpstore_data["add_processing_information"] = processing_information_details

        store_response = requests.put(
            url_for("api.tmpstore_edit_tmpstore", hash=hash, _external=True),
            headers=get_internal_api_header(),
            json={"data": tmpstore_data}
        )

        if store_response.status_code == 200:
            return redirect(
                url_for("sample.add_rerouter", hash=store_response.json()["content"]["uuid"])
            )

        flash("We have a problem :( %s" % (store_response.json()))


    return render_template(
        "sample/sample/add/step_four.html",
        form=form,
        hash=hash,
    )

@sample.route("add/sample_review/<hash>", methods=["GET", "POST"])
def add_sample_review(hash):
    tmpstore_response = requests.get(
        url_for("api.tmpstore_view_tmpstore", hash=hash, _external=True),
        headers=get_internal_api_header(),
    )

    if tmpstore_response.status_code != 200:
        abort(tmpstore_response.status_code)

    tmpstore_data = tmpstore_response.json()["content"]["data"]

    form = SampleReviewForm()

    if form.validate_on_submit():
        sample_review_details = {
            "quality": form.quality.data,
            "date": str(form.date.data),
            "time": form.time.data.strftime("%H:%M:%S"),
            "conducted_by": form.conducted_by.data,
            "comments": form.comments.data

        }

        tmpstore_data["add_sample_review"] = sample_review_details

        store_response = requests.put(
            url_for("api.tmpstore_edit_tmpstore", hash=hash, _external=True),
            headers=get_internal_api_header(),
            json={"data": tmpstore_data}
        )

        if store_response.status_code == 200:
            return redirect(
                url_for("sample.add_rerouter", hash=store_response.json()["content"]["uuid"])
            )

        flash("We have a problem :( %s" % (store_response.json()))


    return render_template(
        "sample/sample/add/review.html",
        hash=hash,
        form=form
    )


@sample.route("add/custom_attributes/<hash>", methods=["GET", "POST"])
@login_required
def add_custom_atributes(hash):
    tmpstore_response = requests.get(
        url_for("api.tmpstore_view_tmpstore", hash=hash, _external=True),
        headers=get_internal_api_header(),
    )

    if tmpstore_response.status_code != 200:
        abort(tmpstore_response.status_code)

    tmpstore_data = tmpstore_response.json()["content"]["data"]

    # TODO: Extend the query thing to allow for .in when passed a list

    attribute_response = requests.get(
        url_for("api.attribute_query", _external=True),
        json = {},
        headers=get_internal_api_header()
    )

    if attribute_response.status_code != 200:
        abort(attribute_response.status_code)


    form = CustomAttributeSelectForm(attribute_response.json()["content"])

    if form.validate_on_submit():
        flash("Form submitted")



    return render_template(
        "sample/sample/add/step_five.html",
        form=form,
        hash=hash
    )


'''

@sample.route("add/six/<hash>", methods=["GET", "POST"])
@login_required
def add_sample_form(hash):
    attributes = session["%s step_five" % (hash)]

    form = CustomAttributeGeneratedForm(FinalSampleForm(), attributes)

    # Submit if no attributes found.
    if form.validate_on_submit() or len(attributes) == 0:
        # consent_form_id, barcode, collection_date, disposal_instruction, disposal_date, has_donor, donor_select
        step_one = session["%s step_one" % (hash)]
        # checked, consent_id
        step_two = session["%s step_two" % (hash)]
        # sample_type, quantity, type, fixation, storage_type
        step_three = session["%s step_three" % (hash)]
        # protocol_id, sample_status, processing_date, processing_time
        step_four = session["%s step_four" % (hash)]
        # attribute_ids
        step_five = session["%s step_five" % (hash)]

        sample = Sample(
            uuid=uuid.uuid4(),
            biobank_barcode=step_one["barcode"],
            sample_type=step_three["sample_type"],
            collection_date=step_one["collection_date"],
            quantity=step_three["quantity"],
            current_quantity=step_three["quantity"],
            is_closed=False,
            author_id=current_user.id,
            sample_status=step_four["sample_status"],
        )

        db.session.add(sample)
        db.session.flush()

        sdi = SampleDisposalInformation(
            disposal_instruction=step_one["disposal_instruction"],
            disposal_date=step_one["disposal_date"],
            sample_id=sample.id,
            author_id=current_user.id,
        )

        db.session.add(sdi)
        db.session.flush()

        if step_one["has_donor"]:

            std = SampleToDonor(
                sample_id=sample.id,
                donor_id=step_one["donor_select"],
                author_id=current_user.id,
            )

            db.session.add(std)
            db.session.flush()

        if step_three["sample_type"] == "FLU":
            stot = SampleToFluidSampleType(
                sample_id=sample.id,
                sample_type=step_three["type"],
                author_id=current_user.id,
            )
        elif step_three["sample_type"] == "CEL":
            stot = SampleToCellSampleType(
                sample_id=sample.id,
                sample_type=step_three["type"],
                author_id=current_user.id,
            )
        elif step_three["sample_type"] == "MOL":
            stot = SampleToMolecularSampleType(
                sample_id=sample.id,
                sample_type=step_three["type"],
                author_id=current_user.id,
            )
        else:
            abort(400)

        db.session.add(stot)
        db.session.flush()

        for attr in form:
            if hasattr(attr, "render_kw") and attr.render_kw != None:
                if "_custom_val" in attr.render_kw:
                    if attr.type == "StringField":
                        ca_v = SampleToCustomAttributeTextValue(
                            value=attr.data,
                            custom_attribute_id=attr.id,
                            sample_id=samplProtocolTemplateSelectForme.id,
                            author_id=current_user.id,
                        )

                    elif attr.type == "SelectField":
                        ca_v = SampleToCustomAttributeOptionValue(
                            custom_option_id=attr.data,
                            custom_attribute_id=attr.id,
                            sample_id=sample.id,
                            author_id=current_user.id,
                        )
                    else:
                        ca_v = SampleToCustomAttributeNumericValue(
                            value=attr.data,
                            custom_attribute_id=attr.id,
                            sample_id=sample.id,
                            author_id=current_user.id,
                        )

                    db.session.add(ca_v)

        db.session.flush()ProtocolTemplateSelectForm

        spcfta = SamplePatientConsentFormTemplateAssociation(
            sample_id=sample.id,
            template_id=step_one["consent_form_id"],
            consent_id=step_two["consent_id"],
            author_id=current_user.id,
        )

        db.session.add(spcfta)
        db.session.flush()

        for answer in step_two["checked"]:
            spcfaa = SamplePatientConsentFormAnswersAssociation(
                sample_pcf_association_id=spcfta.id,
                author_id=current_user.id,
                checked=answer,
            )

            db.session.add(spcfaa)

        spta = SampleProcessingTemplateAssociation(
            sample_id=sample.id,
            template_id=step_four["protocol_id"],
            processing_time=step_four["processing_time"],
            processing_date=step_four["processing_date"],
            author_id=current_user.id,
        )

        db.session.add(spta)
        db.session.flush()

        db.session.commit()

        clear_session(hash)

        flash("LIMBSMP: ? successfully submitted.")
        return redirect(url_for("sample.index"))

    return render_template("sample/sample/add/step_six.html", form=form, hash=hash)
'''