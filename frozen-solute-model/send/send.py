# send the relavant molecules ranked by DE

compound_ids = """
mobley_6522117
mobley_1352110
mobley_8916409
mobley_7375018
mobley_1743409
mobley_5393242
mobley_3151666
mobley_8713762
mobley_7754849
mobley_1849020
mobley_9617923
mobley_9460824
mobley_6198745
mobley_2402487
mobley_7608435
mobley_3378420
mobley_3318135
mobley_3047364
mobley_1976156
mobley_9281946
mobley_1502181
mobley_1592519
mobley_3572203
mobley_7326706
mobley_6935906
mobley_1323538
mobley_9741965
mobley_8124669
mobley_2197088
mobley_36119
mobley_3802803
mobley_2607611
mobley_5200358
mobley_2518989
mobley_3709920
mobley_4934872
mobley_9015240
mobley_6248915
mobley_3690931
mobley_6338073
mobley_4694328
mobley_2636578
mobley_9897248
mobley_129464
mobley_9407874
mobley_7860938
mobley_6619554
mobley_819018
mobley_5880265
mobley_1017962
mobley_3210206
mobley_4375719
mobley_6081058
mobley_1944394
mobley_7157427
mobley_7417968
mobley_5079234
mobley_7913234
mobley_8514745
mobley_9197172
mobley_352111
mobley_588781
mobley_4759887
mobley_1770205
mobley_2517158
mobley_7859387
mobley_718988
mobley_7912193
mobley_2099370
mobley_1735893
mobley_7203421
mobley_3573480
mobley_4690963
mobley_2725215
mobley_6456034
mobley_2078467
mobley_52782
mobley_1722522
mobley_2390199
mobley_4587267
mobley_1922649
mobley_5890803
mobley_2341732
mobley_3167746
mobley_3201701
mobley_8522124
mobley_1893937
mobley_3546460
mobley_4687447
mobley_5471704
mobley_2269032
mobley_2364370
mobley_3274817
mobley_4762983
mobley_1235151
mobley_6250025
mobley_8207196
mobley_902954
mobley_3525176
mobley_929676
mobley_1827204
mobley_2328633
mobley_6060301
mobley_3686115
mobley_1527293
mobley_4463913
mobley_6896128
mobley_4792268
mobley_2501588
mobley_2487143
mobley_7829570
mobley_4964807
mobley_6334915
mobley_4924862
mobley_5052949
mobley_4603202
mobley_6201330
mobley_6843802
mobley_2958326
mobley_7542832
mobley_8614858
mobley_5747981
mobley_5390332
mobley_6620221
mobley_7176248
mobley_2178600
mobley_49274
mobley_6006813
mobley_5310099
mobley_5759258
mobley_7869158
mobley_8467917
mobley_9626434
mobley_7463408
mobley_7977115
mobley_8492526
mobley_9883303
mobley_3738859
mobley_5282042
mobley_6727159
mobley_7573149
mobley_7943327
mobley_8525830
mobley_2792521
mobley_2881590
mobley_2913224
mobley_4630641
mobley_4936555
mobley_5286200
mobley_7142697
mobley_590519
mobley_7463799
mobley_8809190
mobley_1881249
mobley_2693089
mobley_4043987
mobley_5690766
mobley_6115639
mobley_820789
mobley_8789864
mobley_2929847
mobley_6812653
mobley_8337977
mobley_859464
mobley_1899443
mobley_3359593
mobley_7983227
mobley_9007496
mobley_194273
mobley_2023925
mobley_2316618
mobley_3259411
mobley_3589456
mobley_6055410
mobley_6978427
mobley_7455579
mobley_8668219
mobley_1674094
mobley_1875719
mobley_2183616
mobley_2802855
mobley_2864987
mobley_397645
mobley_4013838
mobley_4609460
mobley_4613090
mobley_4893032
mobley_5973402
mobley_8754702
mobley_8772587
mobley_1019269
mobley_1563176
mobley_2213823
mobley_2609604
mobley_3266352
mobley_3325209
mobley_3639400
mobley_4043951
mobley_5006685
mobley_5123639
mobley_5816127
mobley_6929123
mobley_7227357
mobley_8573194
mobley_9114381
mobley_9624458
mobley_1858644
mobley_2422586
mobley_3414356
mobley_4252724
mobley_4479135
mobley_4983965
mobley_5347550
mobley_550662
mobley_5760563
mobley_6416775
mobley_6917738
mobley_6973347
mobley_6981465
mobley_7360181
mobley_7610437
mobley_8449031
mobley_9671033
mobley_9733743
""".splitlines()

done = """
mobley_1019269
mobley_1563176
mobley_1674094
mobley_1858644
mobley_1875719
mobley_1881249
mobley_1899443
mobley_2023925
mobley_2183616
mobley_2213823
mobley_2422586
mobley_2609604
mobley_2802855
mobley_2864987
mobley_2929847
mobley_3259411
mobley_3639400
mobley_4043951
mobley_6620221
mobley_6929123
mobley_6973347
mobley_6978427
mobley_6981465
mobley_9007496
mobley_9114381
""".splitlines()

done = []


compound_ids = """
mobley_1743409
mobley_1849020
mobley_3318135
mobley_6198745
mobley_6338073
mobley_6522117
mobley_8916409
mobley_9281946
mobley_9741965
""".split()

import os
import sqlite3
import subprocess

con = sqlite3.connect("../frozen_solute_model_new.db")
cur = con.cursor()


for compound_id in compound_ids:

    if compound_id in done:
        continue

    res = cur.execute(
        f"SELECT local_path FROM runs WHERE {compound_id = } AND run_type = 'VacuumCENSO' AND status = 'Received'"
    ).fetchall()

    if not res:
        continue

    local_path = res[0][0]

    print(compound_id)
    print(local_path)

    conformers = dict()
    conformer_energies = dict()

    # copy file
    try:
        subprocess.run(["cp", f"../data/{local_path}/2_OPTIMIZATION.xyz", f"{compound_id}-censo.xyz"], check=True)
    except Exception:
        continue
    num_atoms = int(subprocess.run(["head", "-n", "1", f"{compound_id}-censo.xyz"], capture_output=True, check=True).stdout.decode('UTF-8').strip())

    # split file
    subprocess.run(["split", "-a", '5', '--additional-suffix=.xyz', '-d', '-l', str(num_atoms + 2), f"{compound_id}-censo.xyz", f"{compound_id}."], check=True)

    # clear last
    subprocess.run(["rm", f"{compound_id}-sorted.xyz"], check=False)

    # open file
    with open(f"../data/{local_path}/2_OPTIMIZATION.out") as f:

        # skip header
        f.readline()
        f.readline()

        for line in f:
            line = line.split()
            if not line:
                break

            # if float(line[2]) <= 2:
            #     conformers[line[0]] = float(line[1])
            if 2 < float(line[2]) <= 4:
                conformers[line[0]] = float(line[1])





        print(conformers)

    # sort
    for conformer in sorted(conformers, key=conformers.get):

        # combine files
        subprocess.run([f"grep -lZE ^{conformer}$ {compound_id}.*.xyz | xargs -0 cat >> {compound_id}-sorted.xyz"], shell=True, check=True)

        # double check
        assert int(subprocess.run([f"grep -E ^{conformer}$ {compound_id}-sorted.xyz | wc -l"], shell=True, check=True, capture_output=True).stdout.decode('utf-8')) == 1

        # add energies
        subprocess.run([f"sed -i 's/^{conformer}$/{conformer} {conformers[conformer]}/g' {compound_id}-sorted.xyz"], check=True, shell=True)

        # triple check
        assert int(subprocess.run([f"grep -E ^{conformer}$ {compound_id}-sorted.xyz | wc -l"], shell=True, check=True, capture_output=True).stdout.decode('utf-8')) == 0
        assert int(subprocess.run([f"grep -E '^{conformer} ' {compound_id}-sorted.xyz | wc -l"], shell=True, check=True, capture_output=True).stdout.decode('utf-8')) == 1
