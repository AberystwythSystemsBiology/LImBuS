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

import os
import sys

sys.path.append(os.getcwd())
from app import create_app

import unittest


class BasicTests(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app()
        app.testing = True
        self.app = app.test_client()

    def test_main(self):
        response = self.app.get("/", follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
