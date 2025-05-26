"""
convert3e

converts runs if and only if the conf is the same in step 2a and step 3
"""

import os
import sqlite3
import subprocess

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

censo_paths = cur.execute(
    "SELECT compound_id, local_path FROM runs WHERE run_type = 'CENSO' AND status = 'Received'"
).fetchall()

for i in censo_paths:
    compound_id, censo_path = i
    print(f"{compound_id = }")
    print(f"{censo_path = }")


    # get step 2a conf
    conformers = dict()
    with open(f"data/{censo_path}/2_OPTIMIZATION.out") as f:
        # skip header
        f.readline()
        f.readline()

        for line in f:
            line = line.split()
            if not line:
                break
            conformers[line[0]] = float(line[1])

    step_2a_conf = sorted(conformers, key=conformers.get)[0]
    assert step_2a_conf.startswith("CONF"), step_2a_conf


    # get step 3 conf
    step_3_conf = (
        subprocess.run(
            [f"head -n 2 data/{censo_path}/3_REFINEMENT.xyz | tail -n 1"],
            check=True,
            capture_output=True,
            shell=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    if not step_3_conf.startswith("CONF"):
        print("Step 3 conf does not exist, skipping")
        continue


    print(f"{step_2a_conf = }, {step_3_conf = }")

    if step_2a_conf == step_3_conf:
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenMinEquilCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenMinEquilCENSO'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenForwardCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenForwardCENSO'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenReversedCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenReversedCENSO'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenBarCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenBarCENSO'"
        )
        con.commit()

con.close()
