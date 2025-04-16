import collections
import sqlite3
import subprocess
import sys

import rdkit.Chem.rdmolfiles

HOSTNAME = "katana2"

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

res = cur.execute(
    "SELECT compound_id, smiles FROM molecules \
    WHERE compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'CENSO' AND status = 'Received') \
    AND compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenMinEquilCENSO3') \
    ORDER BY rotatable_bonds ASC, num_atoms ASC LIMIT 1"
)

molecule_id, smiles = res.fetchone()
print(molecule_id, smiles)

res = cur.execute(
    "SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs)"
)
local_path = int(res.fetchone()[0])
print(local_path)

if HOSTNAME == "katana":
    REMOTE_PATH = f"/srv/scratch/z5358697/.automated/{local_path}/"
elif HOSTNAME == "katana2":
    REMOTE_PATH = f"/srv/scratch/z5382435/.automated/{local_path}/"
elif HOSTNAME == "gadi":
    REMOTE_PATH = f"/scratch/cw7/mw7780/.automated/{local_path}/"
else:
    assert False

subprocess.run(["mkdir", "-p", f"data/{local_path}"], check=True)

res = cur.execute(
    f"SELECT local_path FROM runs WHERE compound_id = '{molecule_id}' AND run_type = 'CENSO' LIMIT 1"
)
xyz_path = res.fetchone()[0]
print(xyz_path)
# m = rdkit.Chem.rdmolfiles.MolFromXYZFile("data/{xyz_path}/2_OPTIMIZATION.xyz")
# print(m)
# print(rdkit.Chem.MolToSmiles(m))

# subprocess.run(
#     [
#         f"iqmol",
#         f"FreeSolv/mol2files_sybyl/{molecule_id}.mol2",
#         f"data/{xyz_path}/2_OPTIMIZATION.xyz",
#     ],
#     check=True,
# )

retry = 0
while True:
    print("mol2")
    try:
        subprocess.run(
            [
                f"stdbuf -oL xvfb-run iqmol FreeSolv/mol2files_sybyl/{molecule_id}.mol2 He.xyz > mol2",
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
            print(f"Failing job {molecule_id}")
            cur.execute(
                f"INSERT INTO runs VALUES ('{molecule_id}', 'FrozenMinEquilCENSO3', 'Failed', {local_path}, '{HOSTNAME}', '{REMOTE_PATH}');"
            )
            con.commit()
            con.close()
            sys.exit()

        continue
print("xyz")
try:
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
        assert d[k] == v

subprocess.run(["cp", f"data/{xyz_path}/2_OPTIMIZATION.xyz", "."], check=True)

subprocess.run(
    ["python", "prep.frozen.py", molecule_id, str(local_path), HOSTNAME], check=True
)

subprocess.run(["rm", "2_OPTIMIZATION.xyz"], check=True)

subprocess.run(
    [
        "rsync",
        "-rv",
        f"data/{local_path}/",
        f"{HOSTNAME}:{REMOTE_PATH}",
    ],
    check=True,
)

subprocess.run(
    [
        "ssh",
        HOSTNAME,
        f"cd {REMOTE_PATH} && qsub {local_path}",
    ]
)

subprocess.run(["killall", "iqmol"], check=False)

cur.execute(
    f"INSERT INTO runs VALUES ('{molecule_id}', 'FrozenMinEquilCENSO3', 'Running', {local_path}, '{HOSTNAME}', '{REMOTE_PATH}');"
)
con.commit()
con.close()

# input("Reminder to change the queue type ;)")
