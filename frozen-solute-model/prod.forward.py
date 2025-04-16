# pylint: disable=C0103

import sys
import os
import subprocess

from common import tleap_template
from common import generic_template
from common import prod_io
from common import prod_run
from common import constraint_gpu
from common import katana_gpu, gadi_min_equil

print(sys.argv)
assert len(sys.argv) >= 3, (sys.argv, len(sys.argv))
mobley_id = sys.argv[1]
assert mobley_id.startswith("mobley_")
local_path = sys.argv[2]
assert int(local_path) >= 0
if len(sys.argv) > 3:
    hostname = sys.argv[3]
else:
    hostname = None

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
            constraints=constraint_gpu,
            run=prod_run.format(
                mobley_id=mobley_id, mode="rf", start=0, end=1, step=0.05
            ),
        )
    )

if not hostname:
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(katana_gpu.format())
