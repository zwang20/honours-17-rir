# pylint: disable=C0103

import sys
import os
import subprocess

from common import tleap_template
from common import generic_template
from common import prod_io
from common import prod_run
from common import constraint_frozen
from common import katana_prod, setonix_prod

# 1044
# INSERT INTO runs VALUES ('mobley_1079207', 'FrozenForwardCENSO', 'Planned', 1044, 'katana', '/srv/scratch/z5358697/.automated/1044/');

print(sys.argv)
assert len(sys.argv) == 4, (sys.argv, len(sys.argv))
mobley_id = sys.argv[1]
assert mobley_id.startswith("mobley_")
local_path = sys.argv[2]
assert int(local_path) >= 0
hostname = sys.argv[3]
assert hostname in ('katana', 'katana2', 'setonix')

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
            constraints=constraint_frozen.format(mobley_id=mobley_id),
            run=prod_run.format(
                mobley_id=mobley_id, mode="ff", start=0, end=1, step=0.05
            ),
        )
    )

if hostname in ('katana', 'katana2'):
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(katana_prod.format())
elif hostname == 'setonix':
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(setonix_prod.format())
else:
    assert False
