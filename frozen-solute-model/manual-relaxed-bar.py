#!/usr/bin/python

import os
import sqlite3
import subprocess
import sys

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

res = cur.execute(
    "SELECT compound_id FROM molecules \
    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedBarGAFF') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedForwardGAFF' AND status = 'Received') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedReversedGAFF' AND status = 'Received') \
    ORDER BY rotatable_bonds ASC, num_atoms ASC LIMIT 1"
)

row = res.fetchone()
if row is None:
    print("No more relaxed bars")
    sys.exit()

compound_id = row[0]
print(f"{compound_id = }")

res = cur.execute(
    "SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs)"
)
local_path = int(res.fetchone()[0])
print(f"{local_path = }")

print(
    f"INSERT INTO runs VALUES ('{compound_id}', 'RelaxedBarGAFF', 'Failed', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'RelaxedForwardGAFF'"
)
forward_path = int(res.fetchone()[0])
print(f"{forward_path = }")

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'RelaxedReversedGAFF'"
)
reversed_path = int(res.fetchone()[0])
print(f"{reversed_path = }")

os.makedirs(f"data/{local_path}", exist_ok=True)

# copying files
subprocess.run(["cp", f"data/{forward_path}/rf.fepout", "rf.fepout"], check=True)
if subprocess.run(
    ["cp", f"data/{reversed_path}/rf.fepout", "rr.fepout"],
    check=False,
).returncode:
    subprocess.run(["cp", f"data/{reversed_path}/rr.fepout", "rr.fepout"], check=True)

# calculate bar
subprocess.run(
    ["xvfb-run", "-a", "vmd"],
    input="parsefep -forward rf.fepout -backward rr.fepout -bar".encode("utf-8"),
    check=True,
)
subprocess.run(
    ["mv", "rf.fepout", f"data/{local_path}/"],
    check=True,
)
subprocess.run(
    ["mv", "rr.fepout", f"data/{local_path}/"],
    check=True,
)
subprocess.run(
    ["mv", "ParseFEP.log", f"data/{local_path}/ParseFEP.log"],
    check=True,
)

cur.execute(
    f"INSERT INTO runs VALUES ('{compound_id}', 'RelaxedBarGAFF', 'Received', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)
con.commit()
con.close()
