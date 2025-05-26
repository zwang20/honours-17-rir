import subprocess

for filename in subprocess.run(["ls *-sorted.xyz"], shell=True, capture_output=True, check=True).stdout.decode("utf-8").split():
    with open(filename) as f:
        print(filename)
        confs = set()
        conf_max = -1e10
        for line in f:
            if line.startswith("CONF"):
                line = line.split()
                line[1] = float(line[1])
                assert line[0] not in confs, (f"{line[0]} in conf twice for {filename}")
                confs &= {line[0]}
                assert conf_max <= line[1], (f"{line[1]} < {conf_max} for {filename}")
                conf_max = line[1]

