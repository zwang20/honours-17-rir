#!/usr/bin/python

import os
import sqlite3
import subprocess
import sys

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

res = cur.execute(
    "SELECT compound_id FROM molecules \
    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedBarGAFF5') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedForwardGAFF50' AND status = 'Received') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedReversedGAFF50' AND status = 'Received') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedForwardGAFF51' AND status = 'Received') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'RelaxedReversedGAFF51' AND status = 'Received') \
    LIMIT 1"
)

row = res.fetchone()
if row is None:
    print("No more relaxed bars (5)")
    sys.exit()

compound_id = row[0]
print(f"{compound_id = }")

res = cur.execute(
    "SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs)"
)
local_path = int(res.fetchone()[0])
print(f"{local_path = }")

print(
    f"INSERT INTO runs VALUES ('{compound_id}', 'RelaxedBarGAFF5', 'Failed', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)


res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'RelaxedForwardGAFF50'"
)
forward_path_0 = int(res.fetchone()[0])
print(f"{forward_path_0 = }")

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'RelaxedForwardGAFF51'"
)
forward_path_1 = int(res.fetchone()[0])
print(f"{forward_path_1 = }")

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'RelaxedReversedGAFF50'"
)
reversed_path_0 = int(res.fetchone()[0])
print(f"{reversed_path_0 = }")

res = cur.execute(
    f"SELECT local_path FROM runs \
    WHERE compound_id = '{compound_id}' \
    AND run_type = 'RelaxedReversedGAFF51'"
)
reversed_path_1 = int(res.fetchone()[0])
print(f"{reversed_path_1 = }")

os.makedirs(f"data/{local_path}", exist_ok=True)

# copy files

subprocess.run([f'set -euxo pipefail; cat data/{forward_path_0}/rf.fepout data/{forward_path_1}/rf.fepout > rf.combined.fepout'], check=True, shell=True)
subprocess.run([f'set -euxo pipefail; cat data/{reversed_path_0}/rr.fepout data/{reversed_path_1}/rr.fepout > rr.combined.fepout'], check=True, shell=True)

# calculate bar
subprocess.run(
    ["xvfb-run", "-a", "vmd"],
    input="parsefep -forward rf.combined.fepout -backward rr.combined.fepout -bar".encode("utf-8"),
    check=True,
)
subprocess.run(
    ["rm", "rf.combined.fepout"],
    check=True,
)
subprocess.run(
    ["rm", "rr.combined.fepout"],
    check=True,
)
subprocess.run(
    ["mv", "ParseFEP.log", f"data/{local_path}/ParseFEP.log"],
    check=True,
)

cur.execute(
    f"INSERT INTO runs VALUES ('{compound_id}', 'RelaxedBarGAFF5', 'Received', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)
con.commit()
con.close()
