# pylint: disable=C0103

# usage: prep.frozen.py <compound_id> <local_path> <remote_host>

import collections
import sys
import os
import sqlite3
import subprocess

from common import tleap_template
from common import generic_template
from common import min_io, equil_io
from common import min_run, equil_run
from common import katana_min_equil, gadi_min_equil
from common import constraint_frozen

assert len(sys.argv) == 4, (sys.argv, len(sys.argv))
compound_id = sys.argv[1]
assert compound_id.startswith("mobley_"), compound_id
local_path = sys.argv[2]
assert int(local_path) >= 0, local_path
hostname = sys.argv[3]
assert hostname in ("katana", "katana2", "gadi"), hostname

# database
con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

xyz_path = cur.execute(
    f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'CENSO' LIMIT 1"
).fetchone()[0]

retry = 0
while True:
    print("mol2")
    try:
        subprocess.run(
            [
                f"stdbuf -oL xvfb-run iqmol FreeSolv/mol2files_sybyl/{compound_id}.mol2 He.xyz > mol2",
            ],
            timeout=15,
            capture_output=True,
            shell=True,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pass
    d = collections.defaultdict(dict)
    with open("mol2") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if i < 4:
                continue
            if not line:
                break
            k, v = line.split(maxsplit=1)
            d[k] = v

    try:
        assert d
        break
    except AssertionError:
        retry += 1
        if retry >= 10:
            print(f"Failing job {compound_id}")
            cur.execute(
                f"INSERT INTO runs VALUES ('{compound_id}', 'FrozenMinEquilCENSO3', 'Failed', {local_path}, '{HOSTNAME}', '{REMOTE_PATH}');"
            )
            con.commit()
            con.close()
            sys.exit(1)

        continue

try:
    print("xyz")
    subprocess.run(
        [
            f"xvfb-run iqmol data/{xyz_path}/2_OPTIMIZATION.xyz He.xyz > xyz",
        ],
        timeout=15,
        capture_output=True,
        shell=True,
        check=False,
    )
except subprocess.TimeoutExpired:
    pass

with open("xyz") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if i < 4:
            continue
        if not line:
            break
        k, v = line.split(maxsplit=1)
        assert d[k] == v, (k, d[k], v)

subprocess.run(["killall", "iqmol"], check=False)

subprocess.run(["cp", f"data/{xyz_path}/2_OPTIMIZATION.xyz", "."], check=True)

# copy files
subprocess.run(["cp", f"FreeSolv/mol2files_gaff/{compound_id}.mol2", "."], check=True)
subprocess.run(["chmod", "-x", f"{compound_id}.mol2"], check=True)
subprocess.run(["cp", f"FreeSolv/amber/{compound_id}.frcmod", "."], check=True)

# update coords
subprocess.run(
    [
        "python",
        "update-mol2-with-xyz.py",
        f"{compound_id}.mol2",
        f"2_OPTIMIZATION.xyz",
        f"{compound_id}.new.mol2",
    ],
    check=True,
)
subprocess.run(["mv", f"{compound_id}.new.mol2", f"{compound_id}.mol2"], check=True)

low, high = (0.0, 20.0)
curr = 10.0
while True:
    with open("leap.in", "w", encoding="utf-8") as f:
        f.write(tleap_template.format(mobley_id=compound_id, size=curr))

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
            f"{compound_id}.pdb",
        ],
        check=True,
    )

    # get size
    with open(f"{compound_id}.pdb", encoding="utf-8") as f:
        x, y, z = map(float, f.readline().split(maxsplit=4)[1:4])
        print(x, y, z)

    num_atoms = int(
        subprocess.run(
            [f"cat {compound_id}.pdb | grep ATOM | wc -l"],
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
subprocess.run(["mv", f"{compound_id}.inpcrd", f"data/{local_path}/"], check=True)
subprocess.run(["mv", f"{compound_id}.prmtop", f"data/{local_path}/"], check=True)
subprocess.run(["mv", f"{compound_id}.pdb", f"data/{local_path}/"], check=True)

# clean up files
subprocess.run(["rm", f"{compound_id}.frcmod"], check=True)
subprocess.run(["rm", f"{compound_id}.mol2"], check=True)
subprocess.run(["rm", f"leap.log"], check=True)

# write input files
with open(f"data/{local_path}/min.namd", "w", encoding="utf-8") as f:
    f.write(
        generic_template.format(
            io=min_io.format(mobley_id=compound_id),
            x=x,
            y=y,
            z=z,
            run=min_run,
            mobley_id=compound_id,
            margin=8.0,
            constraints=constraint_frozen.format(mobley_id=compound_id),
        )
    )

with open(f"data/{local_path}/equil.namd", "w", encoding="utf-8") as f:
    f.write(
        generic_template.format(
            io=equil_io.format(mobley_id=compound_id),
            run=equil_run,
            x=x,
            y=y,
            z=z,
            mobley_id=compound_id,
            margin=8.0,
            constraints=constraint_frozen.format(mobley_id=compound_id),
        )
    )

if hostname.startswith("katana"):
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(katana_min_equil.format())
else:
    # assuming gadi
    # sr, normal, sl, bw
    # sapphire rapids, normal, sky lake, broad well
    with open(f"data/{local_path}/{local_path}", "w", encoding="utf-8") as f:
        f.write(gadi_min_equil.format(queue="normalsr"))
