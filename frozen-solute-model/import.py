#!/usr/bin/python

import sqlite3

import rdkit.Chem  # type: ignore[import-untyped]
import rdkit.Chem.Lipinski  # type: ignore[import-untyped]

import json

con = sqlite3.connect("frozen_solute_model.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys = ON")
cur.execute(
    "CREATE TABLE molecules(compound_id VARCHAR(15) PRIMARY KEY, smiles VARCHAR(255) NOT NULL, iupac VARCHAR(255) NOT NULL, experimental_value REAL NOT NULL, experimental_uncertainty REAL NOT NULL, calculated_value REAL NOT NULL, calculated_uncertainty REAL NOT NULL, experimental_reference VARCHAR(255) NOT NULL, calculated_reference VARCHAR(255) NOT NULL, notes VARCHAR(1023), rotatable_bonds INT CHECK (rotatable_bonds >= 0) NOT NULL, num_atoms INT CHECK (num_atoms > 0) NOT NULL) WITHOUT ROWID"
)
with open("database.txt", encoding="utf-8") as f:
    for line in f:
        if line.startswith("#"):
            continue
        line = line.split("; ")
        assert len(line) == 10, (line, len(line))
        smiles = line[1].strip()
        mol = rdkit.Chem.rdmolfiles.MolFromSmiles(smiles)
        num_rotatable_bonds = rdkit.Chem.Lipinski.NumRotatableBonds(mol)
        mol = rdkit.Chem.AddHs(mol)
        num_atoms = len(mol.GetAtoms())
        cur.execute(
            "INSERT INTO molecules VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            line + [num_rotatable_bonds, num_atoms],
        )

cur.execute(
    """
    CREATE TABLE runs(
        compound_id VARCHAR(15) REFERENCES molecules(compound_id) NOT NULL,
        run_type VARCHAR(255) NOT NULL,
        status VARCHAR(15) NOT NULL,
        local_path INTEGER PRIMARY KEY AUTOINCREMENT,
        remote_host VARCHAR(15) NOT NULL,
        remote_path VARCHAR(255) NOT NULL CHECK ((remote_path LIKE '/%') AND (remote_path LIKE '%/'))
    )
    """
)

with open("data.json") as f:
    c = 0
    for i in json.loads(f.read())["runs"]:
        cur.execute(
            "INSERT INTO runs VALUES(?, ?, ?, ?, ?, ?)",
            [f"mobley_{i["mobley_id"]}"]
            + [f"{list(i["molecular_dynamics_run_type"].keys())[0]}GAFF"]
            + [i["status"]]
            + [int(i["local_path"])]
            + [i["remote_host"]]
            + [i["remote_path"]],
        )
        assert int(i["local_path"]) == c, (int(i["local_path"]), c)
        c += 1
con.commit()
