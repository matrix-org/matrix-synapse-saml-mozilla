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
import logging
import os

import pkg_resources
from twisted.web.server import Request, NOT_DONE_YET
from twisted.web.static import File, Registry

logger = logging.getLogger(__name__)


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


class PickUsernameHandler:
    """Handles requests to /_matrix/saml2/pick_username"""

    @staticmethod
    def parse_config(config: dict):
        return None

    def __init__(self, module_api, parsed_config):
        self._module_api = module_api
        self._file_registry = Registry()

    async def handle_request(self, request: Request):
        try:
            await self._do_handle(request)
        except Exception:
            logger.exception("Error handling request %s", request)
            _return_html_error(500, "Internal server error", request)

    async def _do_handle(self, request):
        # if there is no suffix at all, redirect to '/', preserving the query string
        if not request.postpath:
            qsindex = request.uri.find(b"?")
            qs = request.uri[qsindex:] if qsindex >= 0 else b""

            request.setResponseCode(302)
            request.setHeader(b"location", request.path + b"/" + qs)
            request.setHeader(b"Content-Length", b"0")
            request.finish()
            return

        try:
            pathstr = _parse_pathparts(request)
        except Exception as e:
            logger.info(
                "Rejecting unparsable request for %s: %s %s",
                request.postpath,
                type(e),
                e,
            )
            _return_html_error(400, "Bad path", request)
            return

        logger.info("Request for '%s'", pathstr)
        if not pathstr:
            pathstr = "index.html"
        pathstr = os.path.sep.join(["res", pathstr])

        # find the file
        path = pkg_resources.resource_filename("matrix_synapse_saml_mozilla", pathstr)
        logger.info("Render %s", path)

        file_resource = File(path, registry=self._file_registry)
        res = file_resource.render_GET(request)
        if res != NOT_DONE_YET:
            request.write(res)
            request.finish()


pardirbytes = os.path.pardir.encode("ascii")
curdirbytes = os.path.curdir.encode("ascii")


def _parse_pathparts(request: Request) -> str:
    """Join the parts of path in `request.postpath` into a string"""
    # handle '..' in path
    pathstack = []
    for seg in request.postpath:
        # if there is more than one adjacent "/" in the path, the extras will turn
        # up here: remove them
        seg = seg.strip(b"/")
        if not seg or seg == curdirbytes:
            pass
        elif seg == pardirbytes:
            if not pathstack:
                raise Exception("too many '..' in path")
            pathstack = pathstack[:-1]
        else:
            pathstack.append(seg)
    return os.path.sep.join(seg.decode("utf-8", errors="strict") for seg in pathstack)


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
