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
from typing import Optional

from . import create_mapping_provider

logging.basicConfig()


def _make_test_saml_response(
    provider_config: dict,
    source_attribute_value: str,
    display_name: Optional[str] = None
):
    """Create a fake object based off of saml2.response.AuthnResponse

    Args:
        provider_config: The config dictionary used when creating the provider object
        source_attribute_value: The desired value that the mapping provider will
            pull out of the response object to turn into a Matrix UserID.
        display_name: The desired displayname that the mapping provider will pull
            out of the response object to turn into a Matrix user displayname.

    Returns:
        An object masquerading as a saml2.response.AuthnResponse object
    """

    class FakeResponse(object):

        def __init__(self):
            self.ava = {
                provider_config["mxid_source_attribute"]: [source_attribute_value],
            }

            if display_name:
                self.ava["displayName"] = [display_name]

    return FakeResponse()


class SamlUserAttributeTestCase(unittest.TestCase):

    def _attribute_test(
        self,
        input_uid: str,
        input_displayname: Optional[str],
        output_localpart: str,
        output_displayname: Optional[str],
    ):
        """Creates a dummy response, feeds it to the provider and checks the output

        Args:
            input_uid: The value of the mxid_source_attribute that the provider will
                base the generated localpart off of.
            input_displayname: The saml auth response displayName value that the
                provider will generate a Matrix user displayname from.
            output_localpart: The expected mxid localpart.
            output_displayname: The expected matrix displayname.

        """
        provider, config = create_mapping_provider()
        response = _make_test_saml_response(config, input_uid, input_displayname)

        attribute_dict = provider.saml_response_to_user_attributes(response)
        self.assertEqual(attribute_dict["mxid_localpart"], output_localpart)
        self.assertEqual(attribute_dict["displayname"], output_displayname)

    def test_normal_user(self):
        self._attribute_test("john*doe2000#@example.com", None, "john.doe2000", None)

    def test_normal_user_displayname(self):
        self._attribute_test(
            "john*doe2000#@example.com", "Jonny", "john.doe2000", "Jonny"
        )

    def test_multiple_adjacent_symbols(self):
        self._attribute_test("bob%^$&#!bobby@example.com", None, "bob.bobby", None)

    def test_username_does_not_end_with_dot(self):
        """This is allowed in mxid syntax, but is not aesthetically pleasing"""
        self._attribute_test("bob.bobby$@example.com", None, "bob.bobby", None)

    def test_username_no_email(self):
        self._attribute_test("bob.bobby", None, "bob.bobby", None)

    def test_username_starting_with_underscore(self):
        self._attribute_test(
            "_twilight (sparkle)@somewhere.com", None, "twilight.sparkle", None
        )

    def test_existing_user(self):
        provider, config = create_mapping_provider()
        response = _make_test_saml_response(config, "wibble%@wobble.com", None)

        attribute_dict = provider.saml_response_to_user_attributes(response)

        # Simulate a failure on the first attempt
        attribute_dict = provider.saml_response_to_user_attributes(response, failures=1)

        self.assertEqual(attribute_dict["mxid_localpart"], "wibble1")
        self.assertEqual(attribute_dict["displayname"], None)
