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

from ..api import api
from ..api.responses import *

from ..database import db
from flask import request, current_app, jsonify
from ..decorators import token_required

from marshmallow import ValidationError

from .views import (
    new_user_account_schema,
    basic_user_account_schema,
    basic_user_accounts_schema,
    full_user_account_schema,
    edit_user_account_schema,
)

from ..database import UserAccount, UserAccountToken
from uuid import uuid4


@api.route("/auth")
@token_required
def auth_home(tokenuser: UserAccount):
    return success_with_content_response(
        basic_user_accounts_schema.dump(UserAccount.query.all())
    )


@api.route("/auth/user/<id>", methods=["GET"])
@token_required
def auth_view_user(id: int):
    # TODO: Check if admin or if the current user id == id.
    return success_with_content_response(
        full_user_account_schema.dump(UserAccount.query.filter_by(id=id).first_or_404())
    )


@api.route("auth/user/<id>/lock", methods=["PUT"])
@token_required
def auth_lock_user(id: int, tokenuser: UserAccount):
    user = UserAccount.query.filter_by(id=id).first()

    if not user:
        return {"success": False, "messages": "There's an issue here"}, 417

    user.is_locked = not user.is_locked
    user.editor_id = tokenuser.id
    db.session.add(user)
    db.session.commit()
    db.session.flush()

    return success_with_content_response(full_user_account_schema.dump(user))


@api.route("/auth/user/new_token", methods=["GET"])
@token_required
def auth_new_token(tokenuser: UserAccount):
    new_token = str(uuid4())
    uat = UserAccountToken.query.filter_by(user_id=tokenuser.id).first()
    if uat != None:
        uat.token = new_token
    else:
        uat = UserAccountToken(user_id=tokenuser.id, token=new_token)

    db.session.add(uat)
    db.session.commit()

    return {"success": True, "content": {"token": new_token}}


@api.route("/auth/user/<id>/edit", methods=["PUT"])
@token_required
def auth_edit_user(id: int, tokenuser: UserAccount):
    values = request.get_json()

    if not values:
        return no_values_response()

    try:
        result = edit_user_account_schema.load(values)
    except ValidationError as err:
        return validation_error_response(err)

    user = UserAccount.query.filter_by(id=id).first_or_404()

    for attr, value in values.items():
        setattr(user, attr, value)

    try:
        db.session.add(user)
        db.session.commit()
        db.session.flush()
        return success_with_content_response(basic_user_account_schema.dump(user))
    except Exception as err:
        return transaction_error_response(err)


@api.route("/auth/user/new", methods=["POST"])
@token_required
def auth_new_user(tokenuser: UserAccount) -> dict:
    """Add a new user account endpoint.
    ---
    post:
      description: Submit a new user account
      responses:
        200:
          content:
            application/json:
              schema: NewUserAccountSchema
    """
    values = request.get_json()

    if not values:
        return no_values_response()

    try:
        result = new_user_account_schema.load(values)
    except ValidationError as err:
        return validation_error_response(err)

    new_user_account = UserAccount(**result)
    new_user_account.created_by = tokenuser.id

    try:
        db.session.add(new_user_account)
        db.session.commit()
        db.session.flush()
        return success_with_content_response(
            basic_user_account_schema.dump(new_user_account)
        )
    except Exception as err:
        return transaction_error_response(err)
