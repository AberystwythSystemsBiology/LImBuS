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

from ...database import db, Base
from ...mixins import RefAuthorMixin, RefEditorMixin, UniqueIdentifierMixin
from ..enums import (
    SampleBaseType,
    SampleStatus,
    DisposalInstruction,
    Colour,
    SampleSource,
    BiohazardLevel,
)


class Sample(Base, UniqueIdentifierMixin, RefAuthorMixin, RefEditorMixin):
    __versioned__ = {}
    barcode = db.Column(db.Text)

    source = db.Column(db.Enum(SampleSource))

    status = db.Column(db.Enum(SampleStatus))
    colour = db.Column(db.Enum(Colour))

    biohazard_level = db.Column(db.Enum(BiohazardLevel))

    comments = db.Column(db.Text, nullable=True)

    quantity = db.Column(db.Float, nullable=False)
    remaining_quantity = db.Column(db.Float, nullable=False)

    site_id = db.Column(db.Integer, db.ForeignKey("siteinformation.id"))

    base_type = db.Column(db.Enum(SampleBaseType))

    sample_to_type_id = db.Column(db.Integer, db.ForeignKey("sampletotype.id"))
    sample_type_information = db.relationship("SampleToType")

    # Consent Information
    # Done -> sample_new_sample_consent
    consent_id = db.Column(
        db.Integer, db.ForeignKey("sampleconsent.id"), nullable=False
    )

    consent_information = db.relationship("SampleConsent", uselist=False)

    # Disposal Information
    # Done -> sample_new_disposal_instructions
    disposal_id = db.Column(db.Integer, db.ForeignKey("sampledisposal.id"))
    disposal_information = db.relationship("SampleDisposal", uselist=False)

    protocol_events = db.relationship("SampleProtocolEvent")

    documents = db.relationship("Document", secondary="sampledocument", uselist=True)
    reviews = db.relationship("SampleReview", uselist=True)

    is_closed = db.Column(db.Boolean, default=False)

    subsamples = db.relationship(
        "Sample",
        secondary="subsampletosample",
        primaryjoin="Sample.id==SubSampleToSample.parent_id",
        secondaryjoin="Sample.id==SubSampleToSample.subsample_id",
        viewonly=True,
    )

    parent = db.relationship(
        "Sample",
        secondary="subsampletosample",
        primaryjoin="Sample.id==SubSampleToSample.subsample_id",
        secondaryjoin="Sample.id==SubSampleToSample.parent_id",
        uselist=False, viewonly=True,
    )

    attributes = db.relationship(
        "AttributeData",
        secondary="sampletocustomattributedata",
        uselist=True
    )

    storage = db.relationship("EntityToStorage", uselist=False)

    donor = db.relationship("Donor", uselist=False, secondary="donortosample")


class SubSampleToSample(Base, RefAuthorMixin, RefEditorMixin):
    __versioned__ = {}
    parent_id = db.Column(db.Integer, db.ForeignKey("sample.id"), primary_key=True)
    subsample_id = db.Column(
        db.Integer, db.ForeignKey("sample.id"), unique=True, primary_key=True
    )


class SampleDisposal(Base, RefAuthorMixin, RefEditorMixin):
    __versioned__ = {}
    instruction = db.Column(db.Enum(DisposalInstruction))
    comments = db.Column(db.Text)
    disposal_date = db.Column(db.Date, nullable=True)
