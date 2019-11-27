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

import re
import string

__version__ = "0.0.1"


class SamlMappingProvider(object):
    def __init__(self):
        mxid_localpart_allowed_characters = set(
            "_-./=" + string.ascii_lowercase + string.digits
        )
        self._dot_replace_pattern = re.compile(
            ("[^%s]" % (re.escape("".join(mxid_localpart_allowed_characters)),))
        )
        self._multiple_to_single_dot_pattern = re.compile(r"\.{2,}")

        self._string_end_dot_pattern = re.compile(r"\.$")

    def mxid_source_to_mxid_localpart(self, mxid_source: str, failures: int = 0) -> str:
        """Maps some text from a SAML response to the localpart of a new mxid

        Args:
            mxid_source (str): The input text from a SAML auth response

            failures (int): How many times a call to this function with this
                mxid_source has resulted in a failure (possibly due to the localpart
                already existing)

        Returns:
            str: The localpart of a new mxid
        """
        # Truncate the username to the first found '@' character to prevent complete
        # emails being leaked
        pos = mxid_source.find("@")
        if pos >= 0:
            mxid_source = mxid_source[:pos]
        mxid_localpart = self._dotreplace_for_mxid(mxid_source)

        # Append suffix integer if last call to this function failed to produce
        # a usable mxid
        return mxid_localpart + (str(failures) if failures else "")

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
    def parse_config(config):
        """Parse the dict provided in the homeserver config.

        We currently do not use any config vars
        """
        pass
