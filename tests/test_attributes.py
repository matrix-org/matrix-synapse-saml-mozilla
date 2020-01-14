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
import re
import time
import unittest

import pkg_resources
from saml2.config import SPConfig
from saml2.response import AuthnResponse
from saml2.sigver import security_context

from synapse.api.errors import RedirectException

from matrix_synapse_saml_mozilla._sessions import username_mapping_sessions

from . import create_mapping_provider

logging.basicConfig()


class FakeResponse:
    def __init__(self, source_uid, display_name):
        self.ava = {
            "uid": [source_uid],
        }

        if display_name:
            self.ava["displayName"] = [display_name]


def _load_test_response() -> AuthnResponse:
    response_xml = pkg_resources.resource_string(
        "tests", "test_saml_response.xml"
    ).decode("utf-8")

    config = SPConfig()
    config.load({})
    assert config.attribute_converters is not None

    response = AuthnResponse(
        sec_context=security_context(config),
        attribute_converters=config.attribute_converters,
        entity_id="https://host/_matrix/saml2/metadata.xml",
        allow_unsolicited=True,
        # tell it not to check the `destination`
        asynchop=False,
    )
    response.loads(response_xml, decode=False, origxml=response_xml)
    response.verify()
    return response


class SamlUserAttributeTestCase(unittest.TestCase):
    def test_get_remote_user_id_from_name_id(self):
        resp = _load_test_response()
        provider = create_mapping_provider({"use_name_id_for_remote_uid": True,})
        remote_user_id = provider.get_remote_user_id(resp, "",)
        self.assertEqual(remote_user_id, "test@domain.com")

    def test_redirect(self):
        """Creates a dummy response, feeds it to the provider and checks that it
        redirects to the username picker.
        """
        provider = create_mapping_provider()
        response = FakeResponse(123435, "Jonny")

        # we expect this to redirect to the username picker
        with self.assertRaises(RedirectException) as cm:
            provider.saml_response_to_user_attributes(response, 0, "http://client/")
        self.assertEqual(cm.exception.location, b"/_matrix/saml2/pick_username/")

        cookieheader = cm.exception.cookies[0]
        regex = re.compile(b"^username_mapping_session=([a-zA-Z]+);")
        m = regex.search(cookieheader)
        if not m:
            self.fail("cookie header %s does not match %s" % (cookieheader, regex))

        session_id = m.group(1).decode("ascii")
        self.assertIn(
            session_id, username_mapping_sessions, "session id not found in map"
        )
        session = username_mapping_sessions[session_id]
        self.assertEqual(session.remote_user_id, 123435)
        self.assertEqual(session.displayname, "Jonny")
        self.assertEqual(session.client_redirect_url, "http://client/")

        # the expiry time should be about 15 minutes away
        expected_expiry = (time.time() + 15 * 60) * 1000
        self.assertGreaterEqual(session.expiry_time_ms, expected_expiry - 1000)
        self.assertLessEqual(session.expiry_time_ms, expected_expiry + 1000)
