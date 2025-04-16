"""
count-rotatable-bonds.py

usage:
python count-rotatable-bonds.py <full_mobley_id>
prints the number of rotatable bonds (u8) <- hopefully
"""

import os  # TODO: use grep instead (its faster)
import sys

import rdkit.Chem  # type: ignore[import-untyped]
import rdkit.Chem.Lipinski  # type: ignore[import-untyped]

assert len(sys.argv) == 2, (sys.argv, len(sys.argv))

with open("database.txt", encoding="utf-8") as f:
    for line in f:
        line = line.split("; ")
        if sys.argv[1] == line[0]:
            mol = rdkit.Chem.rdmolfiles.MolFromSmiles(line[1])
            mol = rdkit.Chem.AddHs(mol)
            print(rdkit.Chem.Lipinski.NumRotatableBonds(mol), end="")
            sys.exit(0)

assert False, "Molecule Not Found"
