"""
prod.relaxed.py

unified python script for relaxed forward and reversed

usage:
prod.relaxed.py <compound_id> <local_path> <hostname> <run_type>
"""

# pylint: disable=C0103

import sys
import os
import subprocess

from common import tleap_template
from common import generic_template
from common import prod_io
from common import prod_run
from common import constraint_gpu
from common import katana_gpu

HOSTNAMES = ("katana", "katana2")

print(sys.argv)
assert len(sys.argv) == 5, (sys.argv, len(sys.argv))
mobley_id = sys.argv[1]
assert mobley_id.startswith("mobley_")
local_path = sys.argv[2]
assert int(local_path) >= 0
hostname = sys.argv[3]
assert hostname in HOSTNAMES
run_type = sys.argv[4]


match run_type:
    case "RelaxedForwardGAFF":
        mode="rf"; start=0; end=1; step=0.05; steps = 1500000
    case "RelaxedReversedGAFF":
        mode="rr"; start=1; end=0; step=-0.05; steps = 1500000
    case "RelaxedForwardGAFF50":
        mode="rf"; start=0; end=0.5; step=0.05; steps = 2500000
    case "RelaxedForwardGAFF51":
        mode="rf"; start=0.5; end=1; step=0.05; steps = 2500000
    case "RelaxedReversedGAFF50":
        mode="rr"; start=1; end=0.5; step=-0.05; steps = 2500000
    case "RelaxedReversedGAFF51":
        mode="rr"; start=0.5; end=0; step=-0.05; steps = 2500000
    case default:
        raise NotImplementedError(f"case {default} not implemented")

# get size
with open(f"data/{local_path}/{mobley_id}.pdb", encoding="utf-8") as f:
    x, y, z = map(float, f.readline().split(maxsplit=4)[1:4])

# relaxed forward
with open(f"data/{local_path}/prod.namd", "w", encoding="utf-8") as f:
    f.write(
        generic_template.format(
            io=prod_io.format(mobley_id=mobley_id),
            mobley_id=mobley_id,
            x=x,
            y=y,
            z=z,
            margin=2.0,
            constraints=constraint_gpu.format(),
            run=prod_run.format(
                mobley_id=mobley_id, mode=mode, start=start, end=end, step=step, steps=steps
            ),
        )
    )

if hostname in ("katana", "katana2"):
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(katana_gpu.format())
else:
    assert False
