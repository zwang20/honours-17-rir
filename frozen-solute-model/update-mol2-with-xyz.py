#!/usr/bin/python

import subprocess
import sys

import rdkit.Chem.rdmolfiles

assert len(sys.argv) == 4, (sys.argv, len(sys.argv))
assert sys.argv[1].endswith('mol2'), sys.argv[1]
assert sys.argv[2].endswith('xyz'), sys.argv[2]
assert sys.argv[3].endswith('mol2'), sys.argv[3]

print("WARNING: DISTANCE UNCHECKED")

with (
    open(sys.argv[1], encoding="utf-8") as input_mol2,
    open(sys.argv[2], encoding="utf-8") as input_xyz,
    open(sys.argv[3], "w", encoding="utf-8") as output_file,
):
    while not (line := input_mol2.readline()).startswith("@<TRIPOS>ATOM"):
        output_file.write(line)
    output_file.write(line)
    num_atoms = int(input_xyz.readline().strip())
    input_xyz.readline()
    counter = 0
    while not (line := input_mol2.readline()).startswith("@<TRIPOS>BOND"):
        xyz_type, new_x_str, new_y_str, new_z_str = input_xyz.readline().split()
        new_x, new_y, new_z = float(new_x_str), float(new_y_str), float(new_z_str)
        line_list = line.split(maxsplit=5)
        assert (
                len(line_list[5]) == 30
        ), f"incorrect length {len(line_list[5])}"  # including newline
        assert xyz_type in line_list[1], f"{xyz_type} not in {line_list[1]}"
        old_x, old_y, old_z = (
            float(line_list[2]),
            float(line_list[3]),
            float(line_list[4]),
        )

        # distance = (
        #         (new_x - old_x) ** 2 + (new_y - old_y) ** 2 + (new_z - old_z) ** 2
        # )
        # assert distance < 0.5

        updated_line = f"{line_list[0]:>7} {line_list[1]:<8}{new_x:> 10.4f}{new_y:> 10.4f}{new_z:> 10.4f} {line_list[5]}"  # pylint: disable=C0301
        print(line, end="")
        print(updated_line, end="")
        assert len(updated_line) == 77, len(updated_line)

        counter += 1
        assert counter <= num_atoms
        output_file.write(updated_line)
    output_file.write(line)
    while line := input_mol2.readline():
        output_file.write(line)

input_line_count = (
    subprocess.run(
        ["wc", "-l", sys.argv[1]], capture_output=True, check=True
    )
    .stdout.decode("utf-8")
    .split()[0]
)
output_line_count = (
    subprocess.run(
        ["wc", "-l", sys.argv[3]], capture_output=True, check=True
    )
    .stdout.decode("utf-8")
    .split()[0]
)

assert input_line_count == output_line_count, (input_line_count, output_line_count)
