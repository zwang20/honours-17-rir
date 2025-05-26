"""
convert3e

converts runs if and only if the conf is the same in step 2a and step 2b
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


    step_2a_conf = (
        subprocess.run(
            [f"head -n 2 data/{censo_path}/2_OPTIMIZATION.xyz | tail -n 1"],
            check=True,
            capture_output=True,
            shell=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    assert step_2a_conf.startswith("CONF"), step_2a_conf


    # get step 2b conf
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

    step_2b_conf = sorted(conformers, key=conformers.get)[0]
    assert step_2b_conf.startswith("CONF"), step_2b_conf


    print(f"{step_2a_conf = }, {step_2b_conf = }")

    if step_2a_conf == step_2b_conf:
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenMinEquilCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenMinEquilCENSO3'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenForwardCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenForwardCENSO3'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenReversedCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenReversedCENSO3'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenBarCENSO3E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenBarCENSO3'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenForwardCENSO50E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenForwardCENSO50'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenReversedCENSO50E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenReversedCENSO50'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenForwardCENSO51E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenForwardCENSO51'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenReversedCENSO51E' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenReversedCENSO51'"
        )
        con.commit()

con.close()
