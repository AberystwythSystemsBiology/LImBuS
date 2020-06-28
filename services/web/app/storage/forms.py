from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    StringField,
    SubmitField,
    FileField,
    ValidationError,
    SelectField,
    IntegerField,
)
from wtforms.validators import DataRequired, Email, EqualTo, URL, ValidationError
import pycountry
from ..setup.forms import post_code_validator

from .models import FixedColdStorageTemps, FixedColdStorageType


class RoomRegistrationForm(FlaskForm):
    room = StringField("Room Number", validators=[DataRequired()])
    building = StringField("Building")
    submit = SubmitField("Register Room")


class NewShelfForm(FlaskForm):
    name = StringField(
        "Shelf Name",
        validators=[DataRequired()],
        description="A descriptive name for the shelf, something like top shelf.",
    )

    submit = SubmitField("Register Shelf")


def NewCryovialBoxForm():
    class StaticForm(FlaskForm):
        serial = StringField("Serial Number", validators=[DataRequired()])
        num_rows = IntegerField("Number of Rows", validators=[DataRequired()])
        num_cols = IntegerField("Number of Columns", validators=[DataRequired()])

    setattr(StaticForm, "submit", SubmitField("Register Cryovial Box"))

    return StaticForm()

class NewCryovialBoxFileUploadForm(FlaskForm):
    serial = StringField("Serial Number", validators=[DataRequired()])
    file = FileField("File", validators=[DataRequired()])
    submit = SubmitField("Upload File")

    

class SiteRegistrationForm(FlaskForm):
    name = StringField("Site Name", validators=[DataRequired()])
    address_line_one = StringField("Address Line1", validators=[DataRequired()])
    address_line_two = StringField("Address Line2")
    city = StringField("Town/City", validators=[DataRequired()])
    county = StringField("County", validators=[DataRequired()])
    country = SelectField(
        "Country",
        validators=[DataRequired()],
        choices=[(country.alpha_2, country.name) for country in pycountry.countries],
    )
    post_code = StringField(
        "Post Code", validators=[DataRequired(), post_code_validator]
    )

    submit = SubmitField("Register Site")


def LongTermColdStorageForm():
    class StaticForm(FlaskForm):
        serial_number = StringField(
            "Serial Number",
            description="Equipment serial number is a serial number that identifies an equipment used in the measuring by its serial number."
            )
        manufacturer = StringField(
            "Manufacturer",
            validators=[DataRequired()],
            description="The storage facility manufacturer."
            )
        temperature = SelectField(
            "Temperature",
            choices=FixedColdStorageTemps.choices(),
            validators=[DataRequired()],
            description="The temperature of the inside of the storage facility."
        )
        type = SelectField(
            "Storage Type",
            choices=FixedColdStorageType.choices(),
            validators=[DataRequired()],
            description="A facility that provides storage for any type of biospecimen and/or biospecimen container."
        )

    setattr(StaticForm, "submit", SubmitField("Register"))

    return StaticForm()


def SampleToBoxForm(samples: list) -> FlaskForm:
    class StaticForm(FlaskForm):
        pass

    samples_choices = []

    for sample in samples:
        samples_choices.append(
            [str(sample.id), "LIMBSMP-%s (%s)" % (sample.id, sample.sample_type)]
        )

    setattr(
        StaticForm,
        "samples",
        SelectField("Sample", choices=samples_choices, validators=[DataRequired()]),
    )

    setattr(StaticForm, "submit", SubmitField("Submit Sample"))

    return StaticForm()
