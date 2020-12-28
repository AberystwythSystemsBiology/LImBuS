# Copyright (C) 2020  Keiron O'Shea <keo7@aber.ac.uk>
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



class NewFluidSampleSchema(ma.Schema):
    fluid_sample_type = EnumField(FluidSampleType)
    fluid_container = EnumField(FluidContainer)


new_fluid_sample_schema = NewFluidSampleSchema()


class NewCellSampleSchema(ma.Schema):
    cell_sample_type = EnumField(CellSampleType)
    tissue_sample_type = EnumField(TissueSampleType)
    fixation_type = EnumField(FixationType)
    cell_container = EnumField(CellContainer)


new_cell_sample_schema = NewCellSampleSchema()


class NewMolecularSampleSchema(ma.Schema):
    molecular_sample_type = EnumField(FluidSampleType)
    fluid_container = EnumField(MolecularSampleType)


new_molecular_sample_schema = NewMolecularSampleSchema()


class SampleTypeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = SampleToType

    id = masql.auto_field()

    flui_type = EnumField(FluidSampleType)
    mole_type = EnumField(MolecularSampleType)
    cell_type = EnumField(CellSampleType)
    tiss_type = EnumField(TissueSampleType)

    author = ma.Nested(BasicUserAccountSchema)
    container_id = masql.auto_field()


sample_type_schema = SampleTypeSchema()
