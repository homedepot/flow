#!/bin/bash

source "../ci/scripts/flow-env.sh"

flow github -o VERSION getversion $ENVIRONMENT

pip3 install setuptools==38.5.2
pip3 install twine==1.10.0
pip3 install wheel==0.30.0

python3 setup.py bdist_wheel

twine upload --config-file scripts/.pypirc -r local -u $PYPI_USER -p $PYPI_PWD dist/*
