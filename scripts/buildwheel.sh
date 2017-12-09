#!/bin/bash

source "../ci/scripts/flow-env.sh"

flow github -o VERSION getversion $ENVIRONMENT

python3 setup.py bdist_wheel

twine upload --config-file scripts/.pypirc -r local -u $PYPI_USER -p $PYPI_PWD dist/*
