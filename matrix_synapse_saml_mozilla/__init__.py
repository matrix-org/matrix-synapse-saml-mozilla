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

from matrix_synapse_saml_mozilla.mapping_provider import SamlMappingProvider
from matrix_synapse_saml_mozilla.username_picker import pick_username_resource

__version__ = "0.1.dev1"

__all__ = ["SamlMappingProvider", "pick_username_resource"]
