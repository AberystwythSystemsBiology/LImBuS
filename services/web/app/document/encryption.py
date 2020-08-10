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

import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DOCUMENT_KEY = "TEST"
DOCUMENT_SALT = "TESTSALT"

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=bytes(DOCUMENT_SALT, "utf8"),
    iterations=100000,
    backend=default_backend(),
)

key = base64.urlsafe_b64encode(kdf.derive(bytes(DOCUMENT_KEY, "utf8")))
f = Fernet(key)


def encrypt_document(b_obj: bytes) -> dict:
    def _calculate_checksum(b_obj) -> str:
        return hashlib.md5(b_obj).hexdigest()

    token = f.encrypt(b_obj)

    return _calculate_checksum(b_obj), token


def decrypt_document(b_obj: bytes, checksum: str) -> dict:
    def _validate_checksum(b_obj: bytes, checksum: str) -> bool:
        return hashlib.md5(b_obj).hexdigest() == checksum

    doc = f.decrypt(b_obj)

    if _validate_checksum(doc, checksum):
        return doc
