"""
convert3

converts runs if and only if the conf is the same in step 2 and 3
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

    step_2_conf = (
        subprocess.run(
            [f"head -n 2 data/{censo_path}/2_OPTIMIZATION.xyz | tail -n 1"],
            check=True,
            capture_output=True,
            shell=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )
    assert step_2_conf.startswith("CONF"), step_2_conf

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

    if step_2_conf == step_3_conf:
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenMinEquilCENSO3' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenMinEquilCENSO'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenForwardCENSO3' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenForwardCENSO'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenReversedCENSO3' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenReversedCENSO'"
        )
        cur.execute(
            f"UPDATE runs SET run_type = 'FrozenBarCENSO3' WHERE compound_id = '{compound_id}' AND run_type = 'FrozenBarCENSO'"
        )
        con.commit()

con.close()
