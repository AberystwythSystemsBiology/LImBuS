from app import db
from ..enums import *

class SubSampleToSample(db.Model):
    __tablename__ = "subsample_to_samples"
    id = db.Column(db.Integer, primary_key=True)

    subsample_type = db.Column(db.Enum(SubSampleType))
    parent_sample = db.Column(db.Integer, db.ForeignKey("samples.id"))

    creation_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    update_date = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now(),
        nullable=False,
    )
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))