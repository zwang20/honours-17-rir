#!/usr/bin/python


"SELECT * FROM molecules WHERE compound_id in (SELECT compound_id FROM runs WHERE run_type = 'RelaxedBarGAFF') AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'FrozenBarCENSO');"

import collections
import csv
import sqlite3
import subprocess

from common import get_energy_from_fepout

print(
    "id;smiles;iupac;experimental;mobley;relaxed_forward_gaff;relaxed_reversed_gaff;relaxed_hysteresis_gaff;relaxed_bar_gaff;frozen_forward_censo;frozen_reversed_censo;frozen_hysteresis_censo;frozen_bar_censo;relaxed_forward_gaff2;relaxed_reversed_gaff2;relaxed_hysteresis_gaff2;relaxed_bar_gaff2;frozen_forward_gaff2;frozen_reversed_gaff2;frozen_hysteresis_gaff2;frozen_bar_gaff2"
)

gaff2 = dict()
with open("gaff2.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        gaff2[f"mobley_{row["id"]}"] = row

con = sqlite3.connect("frozen_solute_model_new.db")
cur = con.cursor()

molecules = cur.execute(
    "SELECT * FROM molecules \
    WHERE compound_id in (SELECT compound_id FROM runs WHERE run_type = 'CREST' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'CENSO' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'RelaxedForwardGAFF' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'RelaxedReversedGAFF' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'RelaxedBarGAFF' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'VacuumCREST' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'VacuumCENSO' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'FrozenForwardCENSO3' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'FrozenReversedCENSO3' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'FrozenBarCENSO3' AND status = 'Received') \
    AND compound_id in (SELECT compound_id FROM runs WHERE run_type = 'ORCA' AND status = 'Received') "
).fetchall()
# print(molecules[1])
d = dict()

for compound_id, smiles, iupac, experimental, _, mobley, _, _, _, _, _, _ in molecules:

    orca_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'ORCA' LIMIT 1"
    ).fetchone()[0]
    censo = (
        float(
            subprocess.run(
                ["grep", "Final Gibbs free energy", f"data/{orca_path}/censo.out"],
                check=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .split()[5]
        )
        * 627.509474
    )
    vacuum_censo = (
        float(
            subprocess.run(
                [
                    "grep",
                    "Final Gibbs free energy",
                    f"data/{orca_path}/vacuum_censo.out",
                ],
                check=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .split()[5]
        )
        * 627.509474
    )
    correction = vacuum_censo - censo

    relaxed_forward_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'RelaxedForwardGAFF' LIMIT 1"
    ).fetchone()[0]
    relaxed_forward_gaff = get_energy_from_fepout(
        f"data/{relaxed_forward_path}/rf.fepout"
    )

    relaxed_reversed_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'RelaxedReversedGAFF' LIMIT 1"
    ).fetchone()[0]
    try:
        relaxed_reversed_gaff = get_energy_from_fepout(
            f"data/{relaxed_reversed_path}/rr.fepout"
        )
    except subprocess.CalledProcessError:
        relaxed_reversed_gaff = get_energy_from_fepout(
            f"data/{relaxed_reversed_path}/rf.fepout"
        )

    relaxed_hysteresis_gaff = relaxed_forward_gaff + relaxed_reversed_gaff

    relaxed_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'RelaxedBarGAFF' LIMIT 1"
    ).fetchone()[0]

    try:
        relaxed_bar_gaff = float(
            subprocess.run(
                ["tail", "-n1", f"data/{relaxed_path}/ParseFEP.log"],
                check=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .split()[6]
        )
    except IndexError:
        continue

    frozen_forward_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'FrozenForwardCENSO3' LIMIT 1"
    ).fetchone()[0]
    frozen_forward_censo = get_energy_from_fepout(
        f"data/{frozen_forward_path}/ff.fepout"
    )

    frozen_reversed_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'FrozenReversedCENSO3' LIMIT 1"
    ).fetchone()[0]
    frozen_reversed_censo = get_energy_from_fepout(
        f"data/{frozen_reversed_path}/fr.fepout"
    )

    frozen_hysteresis_censo = frozen_forward_censo + frozen_reversed_censo

    frozen_path = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'FrozenBarCENSO3' LIMIT 1"
    ).fetchone()[0]

    try:
        frozen_bar_censo = float(
            subprocess.run(
                ["tail", "-n1", f"data/{frozen_path}/ParseFEP.log"],
                check=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .split()[6]
        )

    except IndexError:
        continue

    if compound_id in gaff2:
        d2 = gaff2[compound_id]
    else:
        d2 = collections.defaultdict(lambda: None)

    d[compound_id] = tuple(
        map(
            str,
            (
                smiles,
                iupac,
                experimental,
                mobley,
                relaxed_forward_gaff,
                relaxed_reversed_gaff,
                relaxed_hysteresis_gaff,
                relaxed_bar_gaff,
                frozen_forward_censo,
                frozen_reversed_censo,
                frozen_hysteresis_censo,
                frozen_bar_censo,
                censo,
                vacuum_censo,
                correction,
                frozen_bar_censo + correction,
                d2["r fwd"],
                d2["r rev"],
                d2["r hist"],
                d2["r bar"],
                d2["f fwd"],
                d2["f rev"],
                d2["f hist"],
                d2["f bar"],
            ),
        )
    )
    print(";".join(d[compound_id]))

# r fwd,r rev,r hist,r ave,r bar,r diff,f fwd,f rev,f hist,f ave,f bar,f diff
print(
    "id;smiles;iupac;experimental;mobley;relaxed_forward_gaff;relaxed_reversed_gaff;relaxed_hysteresis_gaff;relaxed_bar_gaff;frozen_forward_censo;frozen_reversed_censo;frozen_hysteresis_censo;frozen_bar_censo;sp_censo;sp_vacuum_censo;correction;corrected_frozen_bar_censo;relaxed_forward_gaff2;relaxed_reversed_gaff2;relaxed_hysteresis_gaff2;relaxed_bar_gaff2;frozen_forward_gaff2;frozen_reversed_gaff2;frozen_hysteresis_gaff2;frozen_bar_gaff2"
)
for k, v in d.items():
    print(f"{k};{';'.join(v)}")
