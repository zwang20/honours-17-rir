# pylint: disable=C0103

import sys
import os
import subprocess

from common import tleap_template
from common import generic_template
from common import min_io, equil_io
from common import min_run, equil_run
from common import katana_min_equil, gadi_min_equil

assert len(sys.argv) >= 3, (sys.argv, len(sys.argv))
mobley_id = sys.argv[1]
assert mobley_id.startswith("mobley_")
local_path = sys.argv[2]
assert int(local_path) >= 0
if len(sys.argv) > 3:
    hostname = sys.argv[3]
else:
    hostname = None

# copy files
subprocess.run(["cp", f"FreeSolv/mol2files_gaff/{mobley_id}.mol2", "."], check=True)
subprocess.run(["chmod", "-x", f"{mobley_id}.mol2"], check=True)
subprocess.run(["cp", f"FreeSolv/amber/{mobley_id}.frcmod", "."], check=True)

low, high = (0.0, 20.0)
curr = 10.0
while True:
    with open("leap.in", "w", encoding="utf-8") as f:
        f.write(tleap_template.format(mobley_id=mobley_id, size=curr))

    # solvate molecule
    subprocess.run(
        ["tleap", "-s", "-f", "leap.in"],
        capture_output=True,
        check=True,
    )

    # add beta to molecule
    subprocess.run(
        [
            "sed",
            "-i",
            "/MOL/s/1\\.00  0\\.00/1.00  1.00/g",
            f"{mobley_id}.pdb",
        ],
        check=True,
    )

    # get size
    with open(f"{mobley_id}.pdb", encoding="utf-8") as f:
        x, y, z = map(float, f.readline().split(maxsplit=4)[1:4])
        print(x, y, z)

    num_atoms = int(
        subprocess.run(
            [f"cat {mobley_id}.pdb | grep ATOM | wc -l"],
            shell=True,
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")
    )

    print(num_atoms, curr)
    if num_atoms > 3000:
        high = curr
        curr = (low + high) / 2
    elif num_atoms < 2900:
        low = curr
        curr = (low + high) / 2
    else:
        break
    assert abs(high - low) > 1e-06, (high, low, abs(high - low), "Does not converge")

# create folder
os.makedirs(f"data/{local_path}", exist_ok=True)

# move files
subprocess.run(["mv", f"{mobley_id}.inpcrd", f"data/{local_path}/"], check=True)
subprocess.run(["mv", f"{mobley_id}.prmtop", f"data/{local_path}/"], check=True)
subprocess.run(["mv", f"{mobley_id}.pdb", f"data/{local_path}/"], check=True)

# clean up files
subprocess.run(["rm", f"{mobley_id}.frcmod"], check=True)
subprocess.run(["rm", f"{mobley_id}.mol2"], check=True)
subprocess.run(["rm", f"leap.log"], check=True)

# write input files
with open(f"data/{local_path}/min.namd", "w", encoding="utf-8") as f:
    f.write(
        generic_template.format(
            io=min_io.format(mobley_id=mobley_id),
            x=x,
            y=y,
            z=z,
            run=min_run,
            mobley_id=mobley_id,
            margin=8.0,
            constraints="",
        )
    )

with open(f"data/{local_path}/equil.namd", "w", encoding="utf-8") as f:
    f.write(
        generic_template.format(
            io=equil_io.format(mobley_id=mobley_id),
            run=equil_run,
            x=x,
            y=y,
            z=z,
            mobley_id=mobley_id,
            margin=8.0,
            constraints="",
        )
    )

if not hostname:
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(katana_min_equil.format())
else:
    # assuming gadi
    # sr, normal, sl, bw
    # sapphire rapids, norma, sky lake, broad well
    with  open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(gadi_min_equil.format(queue='normalbw'))
