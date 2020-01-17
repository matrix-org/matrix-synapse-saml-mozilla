import logging
from typing import Optional

from matrix_synapse_saml_mozilla import SamlMappingProvider

logging.basicConfig()


def create_mapping_provider(config_dict: Optional[dict] = None) -> SamlMappingProvider:
    # Default configuration
    if config_dict is None:
        config_dict = {}

    # Convert the config dictionary to a SamlMappingProvider.SamlConfig object
    config = SamlMappingProvider.parse_config(config_dict)

    # Create a new instance of the provider with the specified config
    return SamlMappingProvider(config, None)
