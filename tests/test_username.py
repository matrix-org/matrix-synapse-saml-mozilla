# -*- coding: utf-8 -*-
# Copyright 2019 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import unittest

from . import create_mapping_provider

logging.basicConfig()


class SamlUsernameTestCase(unittest.TestCase):

    def test_normal_user(self):
        provider = create_mapping_provider()

        username = "john*doe2000#@example.com"
        localpart = provider.mxid_source_to_mxid_localpart(username)
        self.assertEqual(localpart, "john.doe2000")

    def test_multiple_adjacent_symbols(self):
        provider = create_mapping_provider()

        username = "bob%^$&#!bobby@example.com"
        localpart = provider.mxid_source_to_mxid_localpart(username)
        self.assertEqual(localpart, "bob.bobby")

    def test_username_does_not_end_with_dot(self):
        """This is allowed in mxid syntax, but is not aesthetically pleasing"""
        provider = create_mapping_provider()

        username = "bob.bobby$@example.com"
        localpart = provider.mxid_source_to_mxid_localpart(username)
        self.assertEqual(localpart, "bob.bobby")

    def test_username_no_email(self):
        provider = create_mapping_provider()

        username = "bob.bobby"
        localpart = provider.mxid_source_to_mxid_localpart(username)
        self.assertEqual(localpart, "bob.bobby")

    def test_username_starting_with_underscore(self):
        provider = create_mapping_provider()

        username = "_twilight (sparkle)@somewhere.com"
        localpart = provider.mxid_source_to_mxid_localpart(username)
        self.assertEqual(localpart, "twilight.sparkle")

    def test_existing_user(self):
        provider = create_mapping_provider()

        username = "wibble%@wobble.com"
        localpart = provider.mxid_source_to_mxid_localpart(username)

        # Simulate a failure on the first attempt
        localpart = provider.mxid_source_to_mxid_localpart(username, failures=1)
        self.assertEqual(localpart, "wibble1")
