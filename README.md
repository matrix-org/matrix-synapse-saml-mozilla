# Synapse Mozilla SAML MXID Mapper 

Custom SAML auth response -> MXID mapping algorithm used during the Mozilla
Matrix trial run.

## Installation

This plugin can be installed via [PyPi](https://pypi.org):

```
pip install matrix-synapse-saml-moz
```

## Usage

Example synapse config:

```yaml
   saml2_config:
     mapping_provider: "saml_mapping_provider.SamlMappingProvider"
```

## Development and Testing

This repository uses `tox` to run linting and tests.

### Linting code

Code is linted with the `flake8` tool. Run `tox -e pep8` to check for linting
errors in the codebase.

### Tests

This repository uses `unittest` to run the tests located in the `tests`
directory. They can be ran with `tox -e tests`.
