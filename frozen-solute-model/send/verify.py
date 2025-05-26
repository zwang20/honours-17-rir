compound_ids = """
mobley_1743409
mobley_1849020
mobley_3318135
mobley_6198745
mobley_6338073
mobley_8916409
mobley_9281946
mobley_9741965
""".strip().splitlines()
compound_ids = ['mobley_1849020', 'mobley_8916409']
template = """#!/bin/bash
#PBS -P cw7
#PBS -l ncpus=16
#PBS -l walltime=02:00:00
#PBS -l mem=64Gb
#PBS -l wd
#PBS -q normalbw
#PBS -l storage=scratch/cw7
#PBS -l jobfs=64Gb
#PBS -j oe
set -euo pipefail

# Load module, always specify version number.
module load gaussian/g16c01

# Must include `#PBS -l storage=scratch/ab12+gdata/yz98` if the job
# needs access to `/scratch/ab12/` and `/g/data/yz98/`. Details on:
# https://opus.nci.org.au/display/Help/PBS+Directives+Explained

g16 < {filename}.com > {filename}.log
"""

# template = """#!/usr/bin/bash
# #PBS -l walltime=12:00:00
# #PBS -l select=cpuflags=avx512_vpopcntdq
# #PBS -l mem=4Gb
# #PBS -l ncpus=1
# #PBS -j oe
# set -e
#
# lscpu
#
# module add orca
#
# cd "$PBS_O_WORKDIR/$PBS_ARRAY_INDEX"
#
# orca {filename}.inp > {filename}.out
# """


import subprocess

# for compound_id in compound_ids:
#     # subprocess.run(["cp", f"sorted/{compound_id}-sorted.xyz", "."], check=True)
#     total_length = int(subprocess.run([f"wc -l < {compound_id}-sorted.xyz"], check=True, capture_output=True, shell=True).stdout.decode('utf-8'))
#     num_atoms = int(subprocess.run(["head", "-n", "1", f"{compound_id}-sorted.xyz"], capture_output=True, check=True).stdout.decode('UTF-8').strip())
#     print(total_length/(num_atoms+2))
#
#     # split file
#     subprocess.run(["split", '--additional-suffix=.xyz', '-d', '-l', str(num_atoms + 2), f"{compound_id}-sorted.xyz", f"{compound_id}."], check=True)
# exit()


filenames = subprocess.run(['ls *.xyz'], shell=True, capture_output=True, check=True).stdout.decode('utf-8').split()

for filename in filenames:
    compound_id_id = '.'.join(filename.split('.')[0:2])
    print(f"cd {compound_id_id}; qsub {compound_id_id}.xyz.sh; cd ..")
    subprocess.run(['mkdir', '-p', compound_id_id])


    with open(filename) as input_file, open(f"{compound_id_id}/{filename}.com", 'w') as com_file, open(f"{compound_id_id}/{filename}.sh", 'w') as job_file:
        input_file.readline()
        com_file.write("%NProcShared=16\n")
        com_file.write("#m062X/6-31G(d) Opt\n")
        com_file.write("\n")
        name = input_file.readline()
        com_file.write(f"{name}")
        com_file.write("\n")
        com_file.write("0  1\n")
        for line in input_file:
            com_file.write(line)
        com_file.write('\n')
        job_file.write(template.format(filename=filename))


    # subprocess.run(['cp', filename, f"{compound_id_id}/"])
    # with open(f"{compound_id_id}/{filename}.inp", 'w') as inp_file, open(f"{compound_id_id}/{filename}.sh", 'w') as job_file:
    #     inp_file.write("! r2SCAN-3c tightSCF Opt\n")
    #     inp_file.write(f"* xyzfile 0 1 {filename}\n")
    #     job_file.write(template.format(filename=filename))



























