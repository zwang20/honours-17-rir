#!/usr/bin/python

import collections
import csv
import os
import sqlite3
import subprocess

from common import katana_orca_template

# solvation = 'SMD(WATER)'
orca_inp_template = """! M062X {basis} FREQ OPT {solvation}
* xyzfile 0 1 {input}
"""

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

molecules = cur.execute(
    "SELECT * FROM molecules \
    WHERE compound_id in (SELECT compound_id FROM runs WHERE run_type = 'CENSO' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'VacuumCENSO' AND status = 'Received') "
).fetchall()

for compound_id, smiles, iupac, experimental, _, mobley, _, _, _, _, _, _ in molecules:
    censo_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'CENSO' LIMIT 1"
    ).fetchone()[0]

    censo_conformer = subprocess.run(["grep", "CONF", f"data/{censo_path}/2_OPTIMIZATION.xyz"], check=True, capture_output=True).stdout.decode('utf-8').split()[0]
    assert censo_conformer.startswith("CONF"), censo_conformer

    vacuum_censo_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'VacuumCENSO' LIMIT 1"
    ).fetchone()[0]

    vacuum_censo_conformer = subprocess.run(["grep", "CONF", f"data/{vacuum_censo_path}/2_OPTIMIZATION.xyz"], check=True, capture_output=True).stdout.decode('utf-8').split()[0]
    assert vacuum_censo_conformer.startswith("CONF"), vacuum_censo_conformer

    if censo_conformer != vacuum_censo_conformer:
        print(compound_id, censo_conformer, vacuum_censo_conformer, smiles, iupac)
        os.makedirs(f"verify/{compound_id}/", exist_ok=True)

        subprocess.run(['cp', f"data/{censo_path}/2_OPTIMIZATION.xyz", f"verify/{compound_id}/censo_input.xyz"], check=True)

        subprocess.run(['python', 'trim_xyz.py', f"verify/{compound_id}/censo_input.xyz"], check=True)

        subprocess.run(['cp', f"data/{vacuum_censo_path}/2_OPTIMIZATION.xyz", f"verify/{compound_id}/vacuum_censo_input.xyz"], check=True)

        subprocess.run(['python', 'trim_xyz.py', f"verify/{compound_id}/vacuum_censo_input.xyz"], check=True)


        basis = "DEF2-TZVP"

        with open(f"verify/{compound_id}/censo.inp", "w") as f:
            f.write(orca_inp_template.format(basis=basis, solvation="SMD(WATER)", input="censo_input.xyz"))

        with open(f"verify/{compound_id}/vacuum_censo.inp", "w") as f:
            f.write(orca_inp_template.format(basis=basis, solvation='', input="vacuum_censo_input.xyz"))

        with open(f"verify/{compound_id}/1", "w") as f:
            f.write(katana_orca_template.format())

