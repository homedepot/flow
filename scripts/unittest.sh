#!/bin/bash

echo "Setting up the environment via ~/.virtualenvs/flow/bin/activate"

if [ -d /root/.virtualenvs ]; then
    . /root/.virtualenvs/ci/bin/activate
elif [ -d /.virtualenvs ] ; then
    . /.virtualenvs/ci/bin/activate
elif [ -d ~/.virtualenvs/flow ] ; then
    . ~/.virtualenvs/flow/bin/activate
elif [ -d ~/.virtualenvs/ci ] ; then
    . ~/.virtualenvs/ci/bin/activate
else
    echo "Cannot locate virutal env directory"
fi

pip install -r requirements.txt
pip install -e flow/
pip list --format=columns

echo "Executing the tests and placing the output in test/results.txt"
mkdir -p test-results
# the --capture=sys allows mocking of sys objects.
py.test -s -v ./tests --capture=sys | tee test-results/results.txt

ret_cd=${PIPESTATUS[0]}
if [ "${ret_cd}" == "0" ]; then
	echo "Unit Tests Passed"
else
	echo "Unit Tests Failed"
fi

deactivate

exit ${ret_cd}
