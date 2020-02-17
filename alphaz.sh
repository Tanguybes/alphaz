#!/bin/sh
export PATH="/opt/intel/intelpython3/bin:$PATH"
export PYTHONPATH="$PWD"
python alpha.py $*
