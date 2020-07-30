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

from ... import db

from ..models import *

from ...auth.views import UserView

from ...attribute.models import *
from ...document.models import Document
from ...processing.models import ProcessingTemplate

from ...patientconsentform.models import *

from ..enums import SampleType


def BasicSampleView(sample_id: int) -> dict:
    sample = db.session.query(Sample).filter(Sample.id == sample_id).first_or_404()

    return {
        "id": sample.id,
        "uuid": sample.uuid,
        "biobank_barcode": sample.biobank_barcode,
        "collection_date": sample.collection_date,
        "sample_status": sample.sample_status,
        "creation_date": sample.creation_date,
        "update_date": sample.update_date,
        "author_information": UserView(sample.author_id),
    }


def SampleView(sample_id: int) -> dict:
    def _get_consent_information(sample_id: int) -> dict:

        cft, spcfta = (
            db.session.query(
                ConsentFormTemplate, SamplePatientConsentFormTemplateAssociation
            )
            .filter(SamplePatientConsentFormTemplateAssociation.sample_id == sample_id)
            .filter(
                ConsentFormTemplate.id
                == SamplePatientConsentFormTemplateAssociation.template_id
            )
            .first_or_404()
        )

        checked_answers = (
            db.session.query(
                SamplePatientConsentFormAnswersAssociation, ConsentFormTemplateQuestion
            )
            .filter(
                SamplePatientConsentFormAnswersAssociation.sample_pcf_association_id
                == spcfta.id
            )
            .filter(
                ConsentFormTemplateQuestion.id
                == SamplePatientConsentFormAnswersAssociation.checked
            )
            .all()
        )

        data = {
            "id": cft.id,
            "name": cft.name,
            "association_id": spcfta.id,
            "version": cft.version,
            "answers": {},
        }

        for _, answer in checked_answers:
            data["answers"][answer.id] = {"question": answer.question}

        return data

    def _get_processing_information(sample_id: int) -> dict:

        template, assoc = (
            db.session.query(ProcessingTemplate, SampleProcessingTemplateAssociation)
            .filter(SampleProcessingTemplateAssociation.sample_id == sample_id)
            .filter(
                ProcessingTemplate.id == SampleProcessingTemplateAssociation.template_id
            )
            .first_or_404()
        )

        data = {
            "id": template.id,
            "name": template.name,
            "processing_time": assoc.processing_time,
            "processing_date": assoc.processing_date,
        }

        return data

    def _not_subsample(sample_id) -> dict:
        subsample = (
            db.session.query(SubSampleToSample)
            .filter(SubSampleToSample.subsample_sample_id == sample_id)
            .first()
        )

        if subsample != None:
            return {"parent_id": subsample.parent_sample_id}

        else:
            return True

    def _get_custom_attributes(sample_id: int) -> dict:
        text_values = (
            db.session.query(CustomAttributes, SampleToCustomAttributeTextValue)
            .filter(SampleToCustomAttributeTextValue.sample_id == sample_id)
            .filter(
                SampleToCustomAttributeTextValue.custom_attribute_id
                == CustomAttributes.id
            )
            .all()
        )
        numeric_values = (
            db.session.query(CustomAttributes, SampleToCustomAttributeNumericValue)
            .filter(SampleToCustomAttributeNumericValue.sample_id == sample_id)
            .filter(
                CustomAttributes.id
                == SampleToCustomAttributeNumericValue.custom_attribute_id
            )
            .all()
        )
        option_values = (
            db.session.query(
                CustomAttributes,
                SampleToCustomAttributeOptionValue,
                CustomAttributeOption,
            )
            .filter(SampleToCustomAttributeOptionValue.sample_id == sample_id)
            .filter(
                CustomAttributeOption.id
                == SampleToCustomAttributeOptionValue.custom_option_id
            )
            .all()
        )

        custom_values = {}

        for attribute, _, value in option_values:
            custom_values[attribute.term] = value.term

        for attribute, value in text_values:
            custom_values[attribute.term] = value.value

        for attribute, value in numeric_values:
            custom_values[attribute.term] = value.value

        return custom_values

    def _get_sample_to_type(sample_type, id) -> dict:
        if sample_type == SampleType.CEL:
            sample_to_type = (
                db.session.query(SampleToCellSampleType)
                .filter(SampleToCellSampleType.sample_id == id)
                .first_or_404()
            )

        elif sample_type == SampleType.FLU:
            sample_to_type = (
                db.session.query(SampleToFluidSampleType)
                .filter(SampleToFluidSampleType.sample_id == id)
                .first_or_404()
            )

        return {"sample_type": sample_type, "storage_type": sample_to_type.sample_type}

    def _get_subsamples(sample_id: int) -> dict:
        subsamples = (
            db.session.query(SubSampleToSample)
            .filter(SubSampleToSample.parent_sample_id == sample_id)
            .all()
        )

        data = {}

        for sample in subsamples:
            data[sample.subsample_sample_id] = BasicSampleView(
                sample.subsample_sample_id
            )

        return data

    sample = db.session.query(Sample).filter(Sample.id == sample_id).first_or_404()
    sample_disposal = (
        db.session.query(SampleDisposalInformation)
        .filter(SampleDisposalInformation.sample_id == sample_id)
        .first_or_404()
    )

    data = {
        "id": sample.id,
        "uuid": sample.uuid,
        "biobank_barcode": sample.biobank_barcode,
        "collection_date": sample.collection_date,
        "sample_status": sample.sample_status,
        "disposal_instruction": sample_disposal.disposal_instruction,
        "disposal_date": sample_disposal.disposal_date,
        "creation_date": sample.creation_date,
        "update_date": sample.update_date,
        "current_quantity": sample.current_quantity,
        "quantity": sample.quantity,
        "author_information": UserView(sample.author_id),
    }

    data["not_subsample"] = _not_subsample(sample.id)

    data["sample_type_info"] = _get_sample_to_type(sample.sample_type, sample.id)

    if data["not_subsample"] == True:
        data["consent_info"] = _get_consent_information(sample.id)
        data["custom_attribute_data"] = _get_custom_attributes(sample.id)

    else:
        # Also get custom attributes
        data["custom_attribute_data"] = _get_custom_attributes(
            data["not_subsample"]["parent_id"]
        )
        data["consent_info"] = _get_consent_information(
            data["not_subsample"]["parent_id"]
        )
    data["processing_info"] = _get_processing_information(sample.id)

    data["subsamples"] = _get_subsamples(sample.id)

    return data
