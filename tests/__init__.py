from typing import Tuple
from matrix_synapse_saml_mozilla import SamlMappingProvider


def create_mapping_provider() -> Tuple[SamlMappingProvider, dict]:
    # Default configuration
    config_dict = {
        "mxid_source_attribute": "uid"
    }

    # Convert the config dictionary to a SamlMappingProvider.SamlConfig object
    config = SamlMappingProvider.parse_config(config_dict)

    # Create a new instance of the provider with the specified config
    # Return the config dict as well for other test methods to use
    return SamlMappingProvider(config), config_dict
