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

from flask_wtf import FlaskForm
from wtforms import FileField, StringField, SubmitField, DecimalField, BooleanField, TextAreaField
from wtforms.validators import DataRequired


class DiagnosticProcedureCreationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    version = StringField("Version")
    description = TextAreaField("Description")
    submit = SubmitField("Submit")

class DiagnosticProcedureVolumeCreationForm(FlaskForm):
    # TODO: Max Length 2
    code = StringField("Code", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Submit")

class DiagnosticProcedureSubVolumeCreationForm(FlaskForm):
    code = StringField("Code", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    reference = StringField("Reference URL")

    submit = SubmitField("Submit")
