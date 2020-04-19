from app import db
from ..enums import *

class SamplePatientConsentFormTemplateAssociation(db.Model):
    __tablename__ = "sample_pcf_associations"

    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(db.Integer, db.ForeignKey("samples.id"))
    template_id = db.Column(db.Integer, db.ForeignKey("consent_form_templates.id"))

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    creation_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)


