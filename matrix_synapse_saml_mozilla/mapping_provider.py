# -*- coding: utf-8 -*-
# Copyright 2020 The Matrix.org Foundation C.I.C.
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
import random
import string
import time
from typing import Set, Tuple

import attr
import saml2.response

import synapse.module_api
from synapse.api.errors import CodeMessageException
from synapse.module_api.errors import RedirectException

from matrix_synapse_saml_mozilla._sessions import (
    SESSION_COOKIE_NAME,
    UsernameMappingSession,
    expire_old_sessions,
    username_mapping_sessions,
)

logger = logging.getLogger(__name__)


MAPPING_SESSION_VALIDITY_PERIOD_MS = 15 * 60 * 1000

# names of attributes in the `ava` property we get from pysaml2
UID_ATTRIBUTE_NAME = (
    "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
)
EMAIL_ATTRIBUTE_NAME = "email"
DISPLAYNAME_ATTRIBUTE_NAME = "displayName"


@attr.s
class SamlConfig(object):
    use_name_id_for_remote_uid = attr.ib(type=bool, default=True)
    domain_block_list = attr.ib(type=Set[str], factory=set)


class SamlMappingProvider(object):
    def __init__(
        self, parsed_config: SamlConfig, module_api: synapse.module_api.ModuleApi
    ):
        """A Mozilla-flavoured, Synapse user mapping provider

        Args:
            parsed_config: A configuration object. The result of self.parse_config
        """
        self._random = random.SystemRandom()
        self._config = parsed_config

        logger.info("Domain block list: %s", self._config.domain_block_list)

    def get_remote_user_id(
        self, saml_response: saml2.response.AuthnResponse, client_redirect_url: str
    ):
        """Extracts the remote user id from the SAML response"""
        if self._config.use_name_id_for_remote_uid:
            name_id = saml_response.name_id
            if not name_id:
                logger.warning("SAML2 response lacks a NameID field")
                raise CodeMessageException(400, "'NameID' not in SAML2 response")
            return name_id.text
        else:
            try:
                return saml_response.ava[UID_ATTRIBUTE_NAME][0]
            except KeyError:
                logger.warning(
                    "SAML2 response lacks a '%s' attribute", UID_ATTRIBUTE_NAME
                )
                raise CodeMessageException(
                    400, "'%s' not in SAML2 response" % (UID_ATTRIBUTE_NAME,)
                )

    def saml_response_to_user_attributes(
        self,
        saml_response: saml2.response.AuthnResponse,
        failures: int,
        client_redirect_url: str,
    ) -> dict:
        """Maps some text from a SAML response to attributes of a new user
        Args:
            saml_response: A SAML auth response object

            failures: How many times a call to this function with this
                saml_response has resulted in a failure

            client_redirect_url: where the client wants to redirect back to

        Returns:
            dict: A dict containing new user attributes. Possible keys:
                * mxid_localpart (str): Required. The localpart of the user's mxid
                * displayname (str): The displayname of the user
        """
        remote_user_id = self.get_remote_user_id(saml_response, client_redirect_url)
        displayname = saml_response.ava.get(DISPLAYNAME_ATTRIBUTE_NAME, [None])[0]

        expire_old_sessions()

        # check the user's emails against our block list
        if EMAIL_ATTRIBUTE_NAME not in saml_response.ava:
            logger.warning(
                "SAML2 response lacks a '%s' attribute", EMAIL_ATTRIBUTE_NAME,
            )
            raise CodeMessageException(
                400, "'%s' not in SAML2 response" % (EMAIL_ATTRIBUTE_NAME,)
            )

        for email in saml_response.ava[EMAIL_ATTRIBUTE_NAME]:
            parts = email.rsplit("@", 1)
            if len(parts) != 2:
                logger.warning(
                    "Rejecting registration from remote user %s with unparsable email %s",
                    remote_user_id,
                    email,
                )
                raise CodeMessageException(403, "Forbidden")

            if parts[1].lower() in self._config.domain_block_list:
                logger.warning(
                    "Rejecting registration from remote user %s with blacklisted email %s",
                    remote_user_id,
                    email,
                )
                raise CodeMessageException(403, "Forbidden")

        # make up a cryptorandom session id
        session_id = "".join(
            self._random.choice(string.ascii_letters) for _ in range(16)
        )

        now = int(time.time() * 1000)
        session = UsernameMappingSession(
            remote_user_id=remote_user_id,
            displayname=displayname,
            client_redirect_url=client_redirect_url,
            expiry_time_ms=now + MAPPING_SESSION_VALIDITY_PERIOD_MS,
        )

        username_mapping_sessions[session_id] = session
        logger.info("Recorded registration session id %s", session_id)

        # Redirect to the username picker
        e = RedirectException(b"/_matrix/saml2/pick_username/")
        e.cookies.append(
            b"%s=%s; path=/" % (SESSION_COOKIE_NAME, session_id.encode("ascii"),)
        )
        raise e

    @staticmethod
    def parse_config(config: dict) -> SamlConfig:
        """Parse the dict provided by the homeserver's config
        Args:
            config: A dictionary containing configuration options for this provider
        Returns:
            SamlConfig: A custom config object
        """
        parsed = SamlConfig()
        if "use_name_id_for_remote_uid" in config:
            parsed.use_name_id_for_remote_uid = config["use_name_id_for_remote_uid"]

        parsed.domain_block_list.update(config.get("bad_domain_list", []))

        domain_block_file = config.get("bad_domain_file")
        if domain_block_file:
            try:
                with open(domain_block_file, encoding="ascii") as fh:
                    parsed.domain_block_list.update(
                        line.strip().lower() for line in fh.readlines()
                    )
            except Exception as e:
                raise Exception(
                    "Error reading domain block file %s: %s" % (domain_block_file, e)
                )

        return parsed

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
        required = {EMAIL_ATTRIBUTE_NAME}
        optional = {UID_ATTRIBUTE_NAME, DISPLAYNAME_ATTRIBUTE_NAME}

        if not config.use_name_id_for_remote_uid:
            required += UID_ATTRIBUTE_NAME

        return required, optional
