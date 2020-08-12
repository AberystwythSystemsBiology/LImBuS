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

from ..database import db, Address, SiteInformation, UserAccount, Sample

from ..api import api
from ..api.responses import *

from .views import (
    new_address_schema,
    new_site_schema,
    basic_address_schema,
    basic_addresses_schema,
    basic_site_schema,
)

from flask import request
from ..decorators import token_required
from marshmallow import ValidationError


@api.route("/misc/panel_data", methods=["GET"])
@token_required
def get_panel_data(tokenuser: UserAccount):
    data = {
        "name": SiteInformation.query.first().name,
        "basic_statistics": {
            "sample_count": Sample.query.count(),
            "user_count": UserAccount.query.count(),
            "site_count": SiteInformation.query.count(),
            "donor_count": 0,
        },
        "sample_statistic": {"sample_type": [], "sample_status": []},
    }
    return success_with_content_response(data)


@api.route("/misc/address/", methods=["GET"])
@token_required
def address_home(tokenuser: UserAccount):
    return success_with_content_response(basic_addresses_schema(Address.query.all()))


@api.route("/misc/address/new", methods=["POST"])
@token_required
def misc_new_address(tokenuser: UserAccount):
    values = request.get_json()

    if values is None:
        return no_values_response()
    try:
        result = new_address_schema.load(values)
    except ValidationError as err:
        return validation_error_response(err)

    new_address = Address(**result)
    new_address.author_id = tokenuser.id

    try:
        db.session.add(new_address)
        db.session.commit()
        db.session.flush()
        return success_with_content_response(basic_address_schema.dumps(new_address))
    except Exception as err:
        return transaction_error_response(err)


@api.route("/misc/site/new", methods=["POST"])
@token_required
def misc_new_site(tokenuser: UserAccount):
    values = request.get_json()

    if values is None:
        return no_values_response()

    try:
        result = new_site_schema.load(values)
    except ValidationError as err:
        return validation_error_response(err)

    new_site = SiteInformation(**result)
    new_site.author_id = tokenuser.id

    try:
        db.session.add(new_site)
        db.session.commit()
        db.session.flush()
        return success_with_content_response(basic_site_schema.dumps(new_site))
    except Exception as err:
        return transaction_error_response(err)
