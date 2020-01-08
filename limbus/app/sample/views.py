from flask import render_template, redirect, url_for, jsonify, request, session
from .models import Sample, Donor, SampleAttribute, SampleAttributeTextualValue
from .forms import SampleAttributeCreationForm, SampleCreationForm, DynamicAttributeSelectForm, p, SampleAttributeTypes
from wtforms import SelectField, StringField, SubmitField, DateField, BooleanField, TextAreaField, TextField
from ..auth.models import User
from flask_login import login_required, current_user
from . import sample
from .. import db


@sample.route("/")
def portal():
    return render_template("sample/index.html")

@sample.route("samples/")
def index():
    samples = db.session.query(Sample, User).filter(Sample.author_id == User.id).all()
    return render_template("sample/information/index.html", samples=samples)

@sample.route("view/<sample_id>", methods=["GET"])
def view(sample_id):
    sample = db.session.query(Sample).filter(Sample.id == sample_id).first()
    text_attr = db.session.query(
        SampleAttribute,
        SampleAttributeTextualValue
    ).filter(
        SampleAttributeTextualValue.sample_id == sample_id
    ).filter(
        SampleAttributeTextualValue.sample_attribute_id == SampleAttribute.id
    ).all()
    return render_template("sample/information/view.html", sample=sample, text_attr=text_attr)

@sample.route("add/", methods=["GET", "POST"])
def add_sample():
    query = db.session.query(SampleAttribute).all()
    conv = {p.number_to_words(x.id) : x.id for x in query}
    attr_selection = DynamicAttributeSelectForm(query)

    if attr_selection.validate_on_submit():
        # TODO: <hack>
        attribute_ids = []
        for attr in attr_selection:
            if attr.id in conv and attr.data == True:
                attribute_ids.append(conv[attr.id])
        # TODO: </endhack>

        session["attribute_ids"] = attribute_ids
        session["conv"] = conv

        return redirect(url_for('sample.add_sample_stwo'))
    return render_template("sample/information/select_attributes.html", form=attr_selection)

@sample.route("add/sample_info", methods=["GET", "POST"])
def add_sample_stwo():
    query = db.session.query(SampleAttribute).filter(SampleAttribute.id.in_(session["attribute_ids"])).all()

    for attr in query:
        if attr.type == SampleAttributeTypes.TEXT:
            setattr(SampleCreationForm, p.number_to_words(attr.id), TextAreaField(attr.term))

    setattr(SampleCreationForm, "submit", SubmitField("Submit"))
    form = SampleCreationForm()

    if form.validate_on_submit():
        sample = Sample(
            sample_type=form.sample_type.data,
            collection_date=form.collection_date.data,
            disposal_instruction=form.disposal_instruction.data,
            author_id=current_user.id
        )

        db.session.add(sample)
        db.session.flush()

        for attr in form:
            if attr.id not in ["csrf_token", "submit", "sample_type", "collection_date", "disposal_instruction"]:
                if attr.type in ["TextAreaField", "StringField"]:
                    attr_value = SampleAttributeTextualValue(
                        value = attr.data,
                        sample_attribute_id = session["conv"][attr.id],
                        sample_id = sample.id,
                        author_id = current_user.id
                    )
                    db.session.add(attr_value)
        db.session.commit()

    return render_template("sample/information/add.html", form=form)

# Attribute Stuff
@sample.route("attribute/")
def attribute_portal():
    sample_attributes = db.session.query(SampleAttribute, User).filter(SampleAttribute.author_id == User.id).all()
    return render_template("sample/attribute/index.html", sample_attributes=sample_attributes)

@sample.route("attribute/add", methods=["GET", "POST"])
def add_attribute():
    form = SampleAttributeCreationForm()
    if form.validate_on_submit():
        sample_attribute = SampleAttribute(
            term = form.term.data,
            type = form.term_type.data,
            author_id = current_user.id
        )

        db.session.add(sample_attribute)
        db.session.commit()

        return redirect(url_for("sample.index"))
    return render_template("sample/attribute/add.html", form=form)

@sample.route("attribute/view/<attribute_id>")
def view_attribute(attribute_id):
    attribute, attribute_user = db.session.query(SampleAttribute, User).filter(
        SampleAttribute.id == attribute_id
    ).filter(SampleAttribute.author_id == User.id).first()
    return render_template("sample/attribute/view.html", attribute=attribute, attribute_user=attribute_user)