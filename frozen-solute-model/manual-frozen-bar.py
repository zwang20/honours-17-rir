#!/usr/bin/python

import os
import sqlite3
import subprocess
import sys

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

res = cur.execute(
    "SELECT compound_id FROM molecules \
    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenBarCENSO') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenForwardCENSO' AND status = 'Received') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenReversedCENSO' AND status = 'Received') \
    ORDER BY rotatable_bonds ASC, num_atoms ASC LIMIT 1"
)

row = res.fetchone()
if row is None:
    print("No more frozen bars")
    sys.exit()

compound_id = row[0]
print(f"{compound_id = }")

res = cur.execute(
    "SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs)"
)
local_path = int(res.fetchone()[0])
print(f"{local_path = }")

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'FrozenForwardCENSO'"
)
forward_path = int(res.fetchone()[0])
print(f"{forward_path = }")

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'FrozenReversedCENSO'"
)
reversed_path = int(res.fetchone()[0])
print(f"{reversed_path = }")

os.makedirs(f"data/{local_path}", exist_ok=True)
# copying files
subprocess.run(["cp", f"data/{forward_path}/ff.fepout", "ff.fepout"], check=True)
subprocess.run(["cp", f"data/{reversed_path}/fr.fepout", "fr.fepout"], check=True)
# calculate bar
subprocess.run(
    ["xvfb-run", "-a", "vmd"],
    input="parsefep -forward ff.fepout -backward fr.fepout -bar".encode("utf-8"),
    check=True,
)
subprocess.run(
    ["mv", "ff.fepout", f"data/{local_path}/"],
    check=True,
)
subprocess.run(
    ["mv", "fr.fepout", f"data/{local_path}/"],
    check=True,
)
subprocess.run(
    ["mv", "ParseFEP.log", f"data/{local_path}/ParseFEP.log"],
    check=True,
)

cur.execute(
    f"INSERT INTO runs VALUES ('{compound_id}', 'FrozenBarCENSO', 'Received', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)
con.commit()
con.close()
