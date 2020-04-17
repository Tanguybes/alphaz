#!/bin/sh
export PATH="/opt/intel/intelpython3/bin:/usr/bin:/usr/bin/geckodriver:$PATH"
export PYTHONPATH="$PWD"

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
cd $SCRIPTPATH

python alphaz.py $*