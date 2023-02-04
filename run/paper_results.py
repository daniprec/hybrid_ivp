"""
Generate all the figures used in the paper. Results section
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

from hybrid_routing.pipeline import Pipeline

list_pipe = [
    Pipeline(p0=(3, 2), pn=(-7, 2), key="Circular"),
    Pipeline(p0=(0, 0), pn=(6, 2), key="FourVortices"),  # Ferraro et al.
]

"""
Create output folder
"""

path_out: Path = Path("output")
if not path_out.exists():
    path_out.mkdir()
# Initialize dict of results
dict_results = {}


"""
Run pipelines
"""

for pipe in list_pipe:
    pipe.solve_zivp(vel=1, time_iter=0.5, time_step=0.025)
    pipe.solve_dnj(num_iter=1000, time_step=0.01)

    k = pipe.key.lower().replace(" ", "-")
    dict_results[k] = pipe.to_dict()

    # Store plot
    plt.figure(figsize=(5, 5))
    pipe.plot(extent=(-8, 4, -4, 6), textbox_pos=(0, -3.5), textbox_align="bottom")
    plt.savefig(path_out / f"results-{k}.png")
    plt.close()

    print(f"Done {k} vectorfield")

"""
Store dictionary
"""
with open(path_out / "results.json", "w") as outfile:
    json.dump(dict_results, outfile)
    json.dump(dict_results, outfile)
