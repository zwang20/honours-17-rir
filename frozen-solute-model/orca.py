#!/usr/bin/python

import sys

from common import orca_inp_template
from common import katana_orca_template

# INSERT 1828

# usage: orca.py <local_path> <remote_host> <functional>
assert len(sys.argv) == 4, sys.argv

local_path = int(sys.argv[1])
hostname = sys.argv[2]
functional = sys.argv[3]

assert hostname in ("katana", "katana2")
assert functional in ("M062X", "r2SCAN-3c")

# basis = "6-31G(d)"
# with open(f"data/{local_path}/censo.xyz") as f:
#     for line in f:
#         element = line.split()[0]
#         if element in ("I",):
#             basis = "DEF2-SVP"

if functional == "M062X":
    basis = "DEF2-TZVP"
elif functional == "r2SCAN-3c":
    # hack
    basis = "tightSCF"
else:
    raise NotImplemented

with open(f"data/{local_path}/censo.inp", "w") as f:
    f.write(orca_inp_template.format(functional=functional, basis=basis, input="censo.xyz"))

with open(f"data/{local_path}/vacuum_censo.inp", "w") as f:
    f.write(orca_inp_template.format(functional=functional, basis=basis, input="vacuum_censo.xyz"))

if hostname in ("katana", "katana2"):
    with open(f"data/{local_path}/{local_path}", "w") as f:
        f.write(katana_orca_template.format())
else:
    assert False, hostname
