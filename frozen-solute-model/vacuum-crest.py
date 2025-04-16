import sys

from common import katana_vacuum_crest

assert len(sys.argv) == 3, (sys.argv, len(sys.argv))
assert sys.argv[1].startswith("data/"), sys.argv[1]
assert "_" in sys.argv[2], sys.argv[2]

with open(f"{sys.argv[1]}", "w") as f:
    f.write(katana_vacuum_crest.format(mobley_id=sys.argv[2]))
