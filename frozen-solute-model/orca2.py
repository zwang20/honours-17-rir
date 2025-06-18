#!/usr/bin/python

import sys

from common import orca_inp_template

katana_orca_template = """#!/usr/bin/bash
#PBS -l walltime=12:00:00
#PBS -l mem=4Gb
#PBS -l ncpus=1
#PBS -j oe
set -e

lscpu

module add orca

cd "$PBS_O_WORKDIR/$PBS_ARRAY_INDEX"

orca orca.inp > orca.out
"""

orca_inp_template_sym = """! {functional} {basis}
%sym
    SymThresh 1.0e-2
    SymRelaxOpt True
    CleanUpGradient True
end
* xyzfile 0 1 {input}
"""

# INSERT 1828

# usage: orca.py <local_path> <remote_host> <functional> <input.xyz>
assert len(sys.argv) == 5, sys.argv

local_path = int(sys.argv[1])
hostname = sys.argv[2]
functional = sys.argv[3]
input_xyz = sys.argv[4]

assert hostname in ("katana", "katana2")
assert input_xyz.endswith(".xyz")

# basis = "6-31G(d)"
# with open(f"data/{local_path}/censo.xyz") as f:
#     for line in f:
#         element = line.split()[0]
#         if element in ("I",):
#             basis = "DEF2-SVP"

if functional == "r2SCAN-3c-opt":
    basis = "TightSCF TightOpt Freq"
    functional = "r2SCAN-3c"
elif functional == "r2SCAN-3c-vtopt":
    basis = "TightSCF VeryTightOpt Freq"
    functional = "r2SCAN-3c"
elif functional == "r2SCAN-3c-opt-sym":
    orca_inp_template = orca_inp_template_sym
    basis = "TightSCF TightOpt Freq"
    functional = "r2SCAN-3c"
else:
    raise NotImplemented

with open(f"data/{local_path}/orca.inp", "w") as f:
    f.write(orca_inp_template.format(functional=functional, basis=basis, input=input_xyz))

if hostname in ("katana", "katana2"):
    with open(f"data/{local_path}/{local_path}", "w") as f:
        f.write(katana_orca_template.format())
else:
    assert False, hostname
