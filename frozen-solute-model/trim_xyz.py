#!/usr/bin/python

import sys

# usage: trim_xyz.py <file.xyz>
assert len(sys.argv) == 2, sys.argv

file_name = sys.argv[1]
lines = []

# read file
with open(file_name) as f:
    # first line
    num_atoms = int(f.readline().strip())
    remarks = f.readline().strip()

    # read atoms
    for _ in range(num_atoms):
        lines.append(f.readline().strip())

    assert len(lines) == num_atoms

# write file
with open(file_name, 'w') as f:
    f.write(f'{num_atoms}\n')
    f.write(f'{remarks}\n')
    for line in lines:
        f.write(f"{line}\n")
