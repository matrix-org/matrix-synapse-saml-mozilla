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

Currently the following options are supported:

 * `use_name_id_for_remote_uid`: if set to `False`, we will use the SAML
   attribute mapped to `uid` to identify the remote user instead of the `NameID`
   from the assertion. `True` by default.

 * `bad_domain_file`: should point a file containing a list of domains (one
   per line); users who have an email address on any of these domains will be
   blocked from registration.

 * `bad_domain_list`: an alternative to `bad_domain_file` allowing the list of
   bad domains to be specified inline in the config.

   If both `bad_domain_file` and `bad_domain_list` are specified, the two lists
   are merged.

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

### Making a release

```
git tag vX.Y
python3 setup.py sdist
twine upload dist/matrix-synapse-saml-mozilla-X.Y.tar.gz
git push origin vX.Y
```
