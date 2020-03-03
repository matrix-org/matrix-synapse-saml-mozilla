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
import html
import json
import logging
import urllib.parse
from typing import Any

import pkg_resources
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Request
from twisted.web.static import File

import synapse.module_api
from synapse.module_api import run_in_background
from synapse.module_api.errors import SynapseError

from matrix_synapse_saml_mozilla._sessions import (
    SESSION_COOKIE_NAME,
    get_mapping_session,
    username_mapping_sessions,
)

"""
This file implements the "username picker" resource, which is mapped as an
additional_resource into the synapse resource tree.

The top-level resource is just a File resource which serves up the static files in the
"res" directory, but it has a couple of children:

   * "submit", which does the mechanics of registering the new user, and redirects the
     browser back to the client URL

    * "check" (TODO): checks if a userid is free.
"""

logger = logging.getLogger(__name__)


def pick_username_resource(
    parsed_config, module_api: synapse.module_api.ModuleApi
) -> Resource:
    """Factory method to generate the top-level username picker resource"""
    base_path = pkg_resources.resource_filename("matrix_synapse_saml_mozilla", "res")
    res = File(base_path)
    res.putChild(b"submit", SubmitResource(module_api))
    res.putChild(b"check", AvailabilityCheckResource(module_api))
    return res


def parse_config(config: dict):
    return None


pick_username_resource.parse_config = parse_config


HTML_ERROR_TEMPLATE = """<!DOCTYPE html>
<html lang=en>
  <head>
    <meta charset="utf-8">
    <title>Error {code}</title>
  </head>
  <body>
     <p>{msg}</p>
  </body>
</html>
"""


def _wrap_for_html_exceptions(f):
    async def wrapped(self, request):
        try:
            return await f(self, request)
        except Exception:
            logger.exception("Error handling request %s" % (request,))
            _return_html_error(500, "Internal server error", request)

    return wrapped


def _wrap_for_text_exceptions(f):
    async def wrapped(self, request):
        try:
            return await f(self, request)
        except Exception:
            logger.exception("Error handling request %s" % (request,))
            body = b"Internal server error"
            request.setResponseCode(500)
            request.setHeader(b"Content-Type", b"text/plain; charset=utf-8")
            request.setHeader(b"Content-Length", b"%i" % (len(body),))
            request.write(body)
            request.finish()

    return wrapped


class AsyncResource(Resource):
    """Extends twisted.web.Resource to add support for async_render_X methods"""

    def render(self, request: Request):
        method = request.method.decode("ascii")
        m = getattr(self, "async_render_" + method, None)
        if not m and method == "HEAD":
            m = getattr(self, "async_render_GET", None)
        if not m:
            return super().render(request)

        async def run():
            with request.processing():
                return await m(request)

        run_in_background(run)
        return NOT_DONE_YET


class SubmitResource(AsyncResource):
    def __init__(self, module_api: synapse.module_api.ModuleApi):
        super().__init__()
        self._module_api = module_api

    @_wrap_for_html_exceptions
    async def async_render_POST(self, request: Request):
        session_id = request.getCookie(SESSION_COOKIE_NAME)
        if not session_id:
            _return_html_error(400, "missing session_id", request)
            return

        session_id = session_id.decode("ascii", errors="replace")
        session = get_mapping_session(session_id)
        if not session:
            logger.info("Session ID %s not found", session_id)
            _return_html_error(403, "Unknown session", request)
            return

        # we don't clear the session from the dict until the ID is successfully
        # registered, so the user can go round and have another go if need be.
        #
        # this means there's theoretically a race where a single user can register
        # two accounts. I'm going to assume that's not a dealbreaker.

        if b"username" not in request.args:
            _return_html_error(400, "missing username", request)
            return
        localpart = request.args[b"username"][0].decode("utf-8", errors="replace")
        logger.info("Registering username %s", localpart)
        try:
            registered_user_id = await self._module_api.register_user(
                localpart=localpart, displayname=localpart
            )
        except SynapseError as e:
            logger.warning("Error during registration: %s", e)
            _return_html_error(e.code, e.msg, request)
            return

        await self._module_api.record_user_external_id(
            "saml", session.remote_user_id, registered_user_id
        )

        del username_mapping_sessions[session_id]

        # delete the cookie
        request.addCookie(
            SESSION_COOKIE_NAME,
            b"",
            expires=b"Thu, 01 Jan 1970 00:00:00 GMT",
            path=b"/",
        )

        self._module_api.complete_sso_login(
            registered_user_id,
            request,
            session.client_redirect_url,
        )


class AvailabilityCheckResource(AsyncResource):
    def __init__(self, module_api: synapse.module_api.ModuleApi):
        super().__init__()
        self._module_api = module_api

    @_wrap_for_text_exceptions
    async def async_render_GET(self, request: Request):
        # make sure that there is a valid mapping session, to stop people dictionary-
        # scanning for accounts
        session_id = request.getCookie(SESSION_COOKIE_NAME)
        if not session_id:
            _return_json({"error": "missing session_id"}, request)
            return

        session_id = session_id.decode("ascii", errors="replace")
        session = get_mapping_session(session_id)
        if not session:
            logger.info("Couldn't find session id %s", session_id)
            _return_json({"error": "unknown session"}, request)
            return

        if b"username" not in request.args:
            _return_json({"error": "missing username"}, request)
            return
        localpart = request.args[b"username"][0].decode("utf-8", errors="replace")
        logger.info("Checking for availability of username %s", localpart)
        try:
            user_id = self._module_api.get_qualified_user_id(localpart)
            registered_id = await self._module_api.check_user_exists(user_id)
            available = registered_id is None
        except Exception as e:
            logger.warning(
                "Error checking for availability of %s: %s %s" % (localpart, type(e), e)
            )
            available = False
        response = {"available": available}
        _return_json(response, request)


def _add_login_token_to_redirect_url(url, token):
    url_parts = list(urllib.parse.urlparse(url))
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update({"loginToken": token})
    url_parts[4] = urllib.parse.urlencode(query)
    return urllib.parse.urlunparse(url_parts)


def _return_html_error(code: int, msg: str, request: Request):
    """Sends an HTML error page"""
    body = HTML_ERROR_TEMPLATE.format(code=code, msg=html.escape(msg)).encode("utf-8")
    request.setResponseCode(code)
    request.setHeader(b"Content-Type", b"text/html; charset=utf-8")
    request.setHeader(b"Content-Length", b"%i" % (len(body),))
    request.write(body)
    try:
        request.finish()
    except RuntimeError as e:
        logger.info("Connection disconnected before response was written: %r", e)


def _return_json(json_obj: Any, request: Request):
    json_bytes = json.dumps(json_obj).encode("utf-8")

    request.setHeader(b"Content-Type", b"application/json")
    request.setHeader(b"Content-Length", b"%d" % (len(json_bytes),))
    request.setHeader(b"Cache-Control", b"no-cache, no-store, must-revalidate")
    request.setHeader(b"Access-Control-Allow-Origin", b"*")
    request.setHeader(
        b"Access-Control-Allow-Methods", b"GET, POST, PUT, DELETE, OPTIONS"
    )
    request.setHeader(
        b"Access-Control-Allow-Headers",
        b"Origin, X-Requested-With, Content-Type, Accept, Authorization",
    )
    request.write(json_bytes)
    try:
        request.finish()
    except RuntimeError as e:
        logger.info("Connection disconnected before response was written: %r", e)
