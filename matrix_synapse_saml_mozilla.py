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

from typing import Tuple
import re
import attr
import string
import saml2.response

__version__ = "0.0.1"


@attr.s
class SamlConfig(object):
    mxid_source_attribute = attr.ib()


class SamlMappingProvider(object):
    def __init__(self, parsed_config: SamlConfig):
        """A Mozilla-flavoured, Synapse user mapping provider

        Args:
            parsed_config: A configuration object. The result of self.parse_config
        """
        self._mxid_source_attribute = parsed_config.mxid_source_attribute

        mxid_localpart_allowed_characters = set(
            "_-./=" + string.ascii_lowercase + string.digits
        )
        self._dot_replace_pattern = re.compile(
            ("[^%s]" % (re.escape("".join(mxid_localpart_allowed_characters)),))
        )
        self._multiple_to_single_dot_pattern = re.compile(r"\.{2,}")
        self._string_end_dot_pattern = re.compile(r"\.$")

    def saml_response_to_user_attributes(
            self,
            saml_response: saml2.response.AuthnResponse,
            failures: int = 0,
    ) -> dict:
        """Maps some text from a SAML response to attributes of a new user

        Args:
            saml_response: A SAML auth response object

            failures: How many times a call to this function with this
                saml_response has resulted in a failure

        Returns:
            dict: A dict containing new user attributes. Possible keys:
                * mxid_localpart (str): Required. The localpart of the user's mxid
                * displayname (str): The displayname of the user
        """
        # The calling function will catch the KeyError if this fails
        mxid_source = saml_response.ava[self._mxid_source_attribute][0]

        # Truncate the username to the first found '@' character to prevent complete
        # emails being leaked
        pos = mxid_source.find("@")
        if pos >= 0:
            mxid_source = mxid_source[:pos]
        mxid_localpart = self._dotreplace_for_mxid(mxid_source)

        # Append suffix integer if last call to this function failed to produce
        # a usable mxid
        localpart = mxid_localpart + (str(failures) if failures else "")

        # Retrieve the display name from the saml response
        displayname = saml_response.ava.get("displayName", [None])[0]

        return {
            "mxid_localpart": localpart,
            "displayname": displayname,
        }

    def _dotreplace_for_mxid(self, username: str) -> str:
        """Replace non-allowed mxid characters with a '.'

        Args:
            username (str): The username to process

        Returns:
            str: The processed username
        """
        username = username.lower()
        username = self._dot_replace_pattern.sub(".", username)

        # regular mxids aren't allowed to start with an underscore either
        username = re.sub("^_", "", username)

        # Change all instances of multiple dots together into a single dot
        username = self._multiple_to_single_dot_pattern.sub(".", username)

        # Remove any trailing dots
        username = self._string_end_dot_pattern.sub("", username)
        return username

    @staticmethod
    def parse_config(config: dict) -> SamlConfig:
        """Parse the dict provided by the homeserver's config
        Args:
            config: A dictionary containing configuration options for this provider
        Returns:
            SamlConfig: A custom config object
        """
        mxid_source_attribute = config.get("mxid_source_attribute", "uid")
        return SamlConfig(mxid_source_attribute)

    @staticmethod
    def get_saml_attributes(config: SamlConfig) -> Tuple[set, set]:
        """Returns the required and optional attributes of a SAML auth response object

        Args:
            config: A SamlConfig object containing configuration options for this provider

        Returns:
            tuple[set,set]: The first set equates to the saml auth response
                attributes that are required for the module to function, whereas the
                second set consists of those attributes which can be used if
                available, but are not necessary
        """
        return {"uid", config.mxid_source_attribute}, {"displayName"}
