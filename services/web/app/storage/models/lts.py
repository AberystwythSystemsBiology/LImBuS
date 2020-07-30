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

from app import db
from ..enums import FixedColdStorageTemps, FixedColdStorageType


class FixedColdStorage(db.Model):
    __tablename__ = "fixed_cold_storage"

    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String)
    manufacturer = db.Column(db.String)

    temperature = db.Column(db.Enum(FixedColdStorageTemps))

    type = db.Column(db.Enum(FixedColdStorageType))

    creation_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))

    update_date = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now(),
        nullable=False,
    )

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class DeviceManualToFixedColdStorage(db.Model):
    __tablename__ = "device_manual_to_fixed_cold_storage"
    id = db.Column(db.Integer, primary_key=True)

    storage_id = db.Column(db.Integer, db.ForeignKey("fixed_cold_storage.id"))
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"))

    creation_date = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    update_date = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now(),
        nullable=False,
    )

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
