import os
import sqlite3
import subprocess

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

res = cur.execute(
    "SELECT compound_id FROM molecules \
    WHERE compound_id NOT IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCENSO') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'VacuumCREST') \
    AND compound_id IN (SELECT compound_id FROM runs WHERE run_type == 'FrozenReversedCENSO') \
    ORDER BY rotatable_bonds ASC LIMIT 1 "
)
molecule_id = res.fetchone()[0]
print(molecule_id)

res = cur.execute(
    "SELECT MIN(local_path + 1) FROM runs WHERE (local_path + 1) NOT IN (SELECT local_path FROM runs)"
)
local_path = int(res.fetchone()[0])
print(local_path)

res = cur.execute(
    "SELECT local_path FROM runs WHERE run_type = 'VacuumCREST' AND compound_id = ?",
    (molecule_id,),
)
vacuum_crest_path = res.fetchone()[0]
print(vacuum_crest_path)

# create path
os.makedirs("data/{}".format(local_path), exist_ok=True)

# copy file
subprocess.run(['cp', f"data/{vacuum_crest_path}/crest_conformers.xyz", f"data/{local_path}/crest_conformers.xyz"],
               check=True)

cur.execute(
    f"INSERT INTO runs VALUES ('{molecule_id}', 'VacuumCENSO', 'Received', {local_path}, 'localhost', '/data/michael/misc/17-rir/frozen-solute-model/data/{local_path}/');"
)
con.commit()
con.close()
