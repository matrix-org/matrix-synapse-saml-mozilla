# Synapse Mozilla SAML MXID Mapper

A Synapse plugin module which allows users to choose their username when they
first log in.

## Installation

This plugin can be installed via [PyPi](https://pypi.org):

```
pip install matrix-synapse-saml-mozilla
```

### Config

Add the following in your Synapse config:

```yaml
   saml2_config:
     user_mapping_provider:
       module: "matrix_synapse_saml_mozilla.SamlMappingProvider"
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
```

### Configuration Options

Synapse allows SAML mapping providers to specify custom configuration through the
`saml2_config.user_mapping_provider.config` option.

There are no options currently supported by this provider.

## Implementation notes

The login flow looks something like this:

![login flow](https://raw.githubusercontent.com/matrix-org/matrix-synapse-saml-mozilla/master/doc/login_flow.svg?sanitize=true)

## Development and Testing

This repository uses `tox` to run linting and tests.

### Linting

Code is linted with the `flake8` tool. Run `tox -e lint` to check for linting
errors in the codebase.

### Tests

This repository uses `unittest` to run the tests located in the `tests`
directory. They can be ran with `tox -e tests`.
