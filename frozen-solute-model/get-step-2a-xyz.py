#!/usr/bin/env python

# Gets the min delta e conf (as opposed to the min delta g conf)

# Usage: get-step-2a-xyz.py

# takes 2_OPTIMIZATION.out and 2_OPTIMIZATION.xyz

# outputs 2_OPTIMIZATION.xyz

import sys

assert len(sys.argv) == 1, sys.argv

# get step 2a conf
conformers = dict()
with open(f"2_OPTIMIZATION.out") as f:
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

file_name = "2_OPTIMIZATION.xyz"


# read file
with open(file_name) as f:
    # first line
    while True:
        lines = []
        num_atoms = int(f.readline().strip())
        remarks = f.readline().strip()

        # read atoms
        for _ in range(num_atoms):
            lines.append(f.readline().strip())

        assert len(lines) == num_atoms

        if remarks == step_2a_conf:
            break


assert remarks == step_2a_conf

# write file
with open(file_name, "w") as f:
    f.write(f"{num_atoms}\n")
    f.write(f"{remarks}\n")
    for line in lines:
        f.write(f"{line}\n")
