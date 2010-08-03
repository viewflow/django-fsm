#!/bin/bash

SCRIPT_DIR=`dirname $0`
ROOT_DIR=`cd $SCRIPT_DIR/.. && pwd`

ENVSPEC=`stat -c %Y $ROOT_DIR/tests/requirements.pip`
ENVTESTSPEC=`stat -c %Y $ROOT_DIR/tests/requirements_test.pip`
ENVTIME=`test -r $ROOT_DIR/.ve/timestamp && stat -c %Y $ROOT_DIR/.ve/timestamp`
set -e

if [ -z "$PIP_DOWNLOAD_CACHE" ]; then
    export PIP_DOWNLOAD_CACHE=$ROOT_DIR/.cache
fi

if [[ $ENVSPEC -gt $ENVTIME || $ENVTESTSPEC -gt $ENVTIME ]]; then
    # Setup environment
    rm -rf $ROOT_DIR/.ve
    mkdir $ROOT_DIR/.ve
    cd $ROOT_DIR/.ve
    virtualenv --no-site-packages $ROOT_DIR/.ve
    source $ROOT_DIR/.ve/bin/activate
    pip install -r $ROOT_DIR/tests/requirements.pip
    pip install -r $ROOT_DIR/tests/requirements_test.pip
    touch $ROOT_DIR/.ve/timestamp
else
    source $ROOT_DIR/.ve/bin/activate
fi

cd $ROOT_DIR
export PYTHONPATH=$ROOT_DIR
python tests/test_runner.py $*
