#!/bin/sh
# Reuse the installed CPython 3.12 and cached Arrow without mutating either cache.
export PYTHONPATH=/home/isa/.cache/uv/archive-v0/oiMcyncRyzJ5wree${PYTHONPATH:+:$PYTHONPATH}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 ARROW_NUM_THREADS=1
exec taskset -c 6,12 /home/isa/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12 "$@"
