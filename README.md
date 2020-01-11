# Synapse Mozilla SAML MXID Mapper

Custom SAML auth response -> MXID mapping algorithm used during the Mozilla
Matrix trial run.

## Installation

This plugin can be installed via [PyPi](https://pypi.org):

```
pip install matrix-synapse-saml-mozilla
```

## Usage

### Config

Add the following in your Synapse config:

```yaml
   saml2_config:
     user_mapping_provider:
       module: "matrix_synapse_saml_mozilla.SamlMappingProvider"
       config:
         mxid_source_attribute: "uid"
```

Also, under the HTTP client `listener`, configure an `additional_resource` as per
the below:

```yaml
listeners:
  - port: <port>
    type: http

    resources:
      - names: [client]

    additional_resources:
      "/_matrix/saml2/pick_username":
        module: "matrix_synapse_saml_mozilla.pick_username_resource"
        config: {}
```

### Configuration Options

Synapse allows SAML mapping providers to specify custom configuration through the
`saml2_config.user_mapping_provider.config` option.

The options supported by this provider are currently:

* `mxid_source_attribute` - The SAML attribute (after mapping via the
                            attribute maps) to use to derive the Matrix
                            ID from. 'uid' by default.

## Development and Testing

This repository uses `tox` to run linting and tests.

### Linting

Code is linted with the `flake8` tool. Run `tox -e pep8` to check for linting
errors in the codebase.

### Tests

This repository uses `unittest` to run the tests located in the `tests`
directory. They can be ran with `tox -e tests`.
