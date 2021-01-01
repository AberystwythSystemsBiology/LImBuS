# Copyright (C) 2020 Keiron O'Shea <keo7@aber.ac.uk>
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


class NewShelfForm(FlaskForm):
    name = StringField(
        "Shelf Name",
        validators=[DataRequired()],
        description="A descriptive name for the shelf, something like top shelf.",
    )

    description = TextAreaField(
        "Shelf Description", description="A brief description of the shelf."
    )

    submit = SubmitField("Register Shelf")



def RackToShelfForm(racks: list) -> FlaskForm:
    class StaticForm(FlaskForm):
        date = DateField(
            "Entry Date", validators=[DataRequired()], default=datetime.today()
        )
        time = TimeField(
            "Entry Time", validators=[DataRequired()], default=datetime.now()
        )
        entered_by = StringField(
            "Entered By",
            description="The initials of the person that entered the sample.",
        )
        submit = SubmitField("Submit")

    choices = []

    for rack in racks:
        choices.append(
            [
                rack["id"],
                "LIMBRACK-%s: %s (%i x %i)"
                % (rack["id"], rack["uuid"], rack["num_rows"], rack["num_cols"]),
            ]
        )

    setattr(
        StaticForm, "racks", SelectField("Sample Rack", choices=choices, coerce=int)
    )

    return StaticForm()