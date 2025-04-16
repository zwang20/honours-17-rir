import math
import sys

from common import katana_censo, setonix_censo

assert len(sys.argv) == 3, (sys.argv, len(sys.argv))
assert sys.argv[1].startswith("data/"), sys.argv[1]
assert (remote_host := sys.argv[2]) in ("katana", "setonix")

file_name = f"{'/'.join(sys.argv[1].split('/')[:-1])}/crest_conformers.xyz"

print(file_name)

with open(file_name) as f:
    a = int(f.readline().strip())

assert a > 0
a += 2

with open(file_name) as f:
    l = len(f.read().splitlines())

assert l % a == 0, (l, a)
ncpus = l // a
ncpus = int(ncpus)

if remote_host == "katana":
    if ncpus > 16:
        ncpus = 16
    assert ncpus <= 16, ncpus
    mem = ncpus * 4
    assert mem <= 124, mem
    with open(f"{sys.argv[1]}", "w") as f:
        f.write(katana_censo.format(ncpus=ncpus, mem=mem))
elif remote_host == "setonix":
    if ncpus > 32:
        ncpus = 32
    assert ncpus <= 32, ncpus
    mem = ncpus * 4
    assert mem <= 128
    with open(f"{sys.argv[1]}", "w") as f:
        f.write(setonix_censo.format(ncpus=ncpus, mem=mem))
