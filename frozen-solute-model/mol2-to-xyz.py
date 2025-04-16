#!/usr/bin/python
import re
import sys

assert len(sys.argv) == 3, (sys.argv, len(sys.argv))
assert sys.argv[1].endswith(".mol2"), sys.argv[1]
assert sys.argv[2].endswith(".xyz"), sys.argv[2]

with (
    open(sys.argv[1]) as input_file,
    open(sys.argv[2], "w") as output_file,
):
    input_file.readline()
    input_file.readline()
    atom_count_ref = int(input_file.readline().split()[0])
    output_file.write(f" {atom_count_ref}\n\n")
    atom_count = 0
    while not input_file.readline().strip().startswith("@<TRIPOS>ATOM"):
        pass
    while not (input_line := input_file.readline().strip()).startswith("@<TRIPOS>BOND"):
        line = input_line.split()
        x, y, z = map(float, line[2:5])
        output_line = f"{re.sub(r'\d+$', '', line[1]).strip(): <2} {x: > 12.6f} {y: > 12.6f} {z: > 12.6f}\n"
        assert len(output_line) == 42, (output_line, len(output_line))
        output_file.write(output_line)
        atom_count += 1
    assert atom_count == atom_count_ref, (atom_count, atom_count_ref)

# crest mobley_3323117.xyz --gfn2 --gbsa h2o -T $(nproc)

# python mol2-to-xyz.py FreeSolv/mol2files_gaff/mobley_1929982.mol2 data/303/mobley_1929982.xyz
