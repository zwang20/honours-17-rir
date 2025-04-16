#!/usr/bin/python
import subprocess
import matplotlib.pyplot as plt
import numpy as np

offset = 0.0
y = [0]
with open("data/4196/ff.fepout")




y = np.concat(
    (
        y,
        np.array(
            list(
                float(i.split()[-1]) + offset
                for i in subprocess.run(
                    ["grep", "-F", "FepEnergy:", f"data/4196/ff.fepout"],
                    capture_output=True,
                )
                .stdout.decode("utf-8")
                .strip()
                .split("\n")
            )
        ),
    ),
)
offset += float(
    subprocess.run(
        [
            "grep",
            "-F",
            "Free energy change for lambda window",
            f"data/4196/ff.fepout",
        ],
        capture_output=True,
    )
    .stdout.decode("utf-8")
    .strip()
    .split()[11]
)
print(len(y))
assert not len(y) % 10
print(y[0:2])
plt.plot((np.arange(600000) + 1) / 600000, y)
plt.show()
