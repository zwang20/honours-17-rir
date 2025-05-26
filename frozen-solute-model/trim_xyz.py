#!/usr/bin/python

import sys

# usage: trim_xyz.py <file.xyz> [CONF]
assert 2 <= len(sys.argv) <= 3, sys.argv

conf = None
if len(sys.argv) > 2:
    assert sys.argv[2].startswith("CONF")
    conf = sys.argv[2]

file_name = sys.argv[1]
lines = []

# read file
with open(file_name) as f:
    # first line
    while True:
        num_atoms = int(f.readline().strip())
        remarks = f.readline().strip()

        # read atoms
        for _ in range(num_atoms):
            lines.append(f.readline().strip())

        assert len(lines) == num_atoms

        if not conf:
            break

        if remarks == conf:
            break

if conf:
    assert remarks == conf

# write file
with open(file_name, "w") as f:
    f.write(f"{num_atoms}\n")
    f.write(f"{remarks}\n")
    for line in lines:
        f.write(f"{line}\n")
