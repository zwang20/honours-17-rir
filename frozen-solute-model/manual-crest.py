import os
import sqlite3
import subprocess

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

res = cur.execute(
    "SELECT * FROM molecules WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'CREST') ORDER BY rotatable_bonds ASC LIMIT 1"
)
molecule_id = res.fetchone()[0]
print(molecule_id)

res = cur.execute(
    "SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs)"
)
local_path = int(res.fetchone()[0])
print(local_path)

cur.execute(
    f"INSERT INTO runs VALUES ('{molecule_id}', 'CREST', 'Received', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)
con.commit()
con.close()

subprocess.run(["mkdir", "-p", f"data/{local_path}"], check=True)
subprocess.run(
    [
        "python",
        "mol2-to-xyz.py",
        f"FreeSolv/mol2files_gaff/{molecule_id}.mol2",
        f"data/{local_path}/{molecule_id}.xyz",
    ],
    check=True,
)

os.chdir(f"data/{local_path}")

subprocess.run(
    [
        f"crest {molecule_id}.xyz --alpb water --chrg 0 --uhf 0 -T 4 --noreftopo | tee crest.log"
    ],
    shell=True,
    check=True,
)
