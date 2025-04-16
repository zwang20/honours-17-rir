import subprocess
import collections

d = collections.defaultdict(dict)

for i in range(987, 1043 + 1):
    file_name = subprocess.run(
        [f"ls data/{i}/{i}.o*"], check=True, shell=True, capture_output=True
    ).stdout.split()[-1]
    with open(file_name) as f:
        for line in f.read().splitlines():
            if line.startswith("Model name:"):
                model_name = line.split(maxsplit=2)[2]
                match model_name:
                    case "Intel(R) Xeon(R) Platinum 8470Q":
                        queue = "normalsr"
                    case "Intel(R) Xeon(R) Platinum 8274 CPU @ 3.20GHz":
                        queue = "normal"
                    case "Intel(R) Xeon(R) Gold 6130 CPU @ 2.10GHz":
                        queue = "normalsl"
                    case "Intel(R) Xeon(R) CPU E5-2690 v4 @ 2.60GHz":
                        queue = "normalbw"
                    case unknown:
                        assert False, unknown
            elif "NCPUs Requested:" in line:
                ncpus = int(line.split()[5])
            elif "Walltime Used:" in line:
                walltime = line.split()[5]
            elif "Service Units:" in line:
                service_units = line.split()[2]

        d[ncpus][queue] = (walltime, service_units)

for k, v in d.items():
    print(k, *v["normalsr"], *v["normal"], *v["normalsl"], *v["normalbw"])
