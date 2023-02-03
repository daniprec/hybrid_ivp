import json
from pathlib import Path

import matplotlib.pyplot as plt
import typer

from hybrid_routing.geometry import DEG2RAD
from hybrid_routing.jax_utils import DNJ, RouteJax
from hybrid_routing.utils.plot import plot_ticks_radians_to_degrees
from hybrid_routing.vectorfields import VectorfieldReal


def main(
    path_json: str,
    key: str = "route_rk",
    path_out: str = "output",
    time_step: float = 3600,
    num_iter: int = 200,
):
    path_out = Path(path_out)

    with open(path_json) as file:
        dict_json: dict = json.load(file)

    # Loop over all runs in dictionary
    for name, dict_run in dict_json.items():
        print("\n---\nBenchmark, run:", name)

        # Generate the vectorfield
        vf = VectorfieldReal.from_folder("./data", dict_run["data"], radians=True)

        # Try to generate the route
        try:
            route = RouteJax(**dict_run[key], geometry=vf.geometry)
        except KeyError:
            raise KeyError(
                "Key not found in dict. Available are: ", ", ".join(dict_run.keys())
            )

        # Plot
        plt.figure(figsize=(5, 5))
        vf.plot(
            x_min=route.x.min() - 5 * DEG2RAD,
            x_max=route.x.max() + 5 * DEG2RAD,
            y_min=route.y.min() - 5 * DEG2RAD,
            y_max=route.y.max() + 5 * DEG2RAD,
            step=1 * DEG2RAD,
            color="grey",
            alpha=0.8,
            do_color=True,
        )
        plt.gca().set_aspect("equal")
        plot_ticks_radians_to_degrees(step=5)

        # Plot source and destination point
        plt.scatter(route.x[0], route.y[0], c="green", s=20, zorder=10)
        plt.scatter(route.x[-1], route.y[-1], c="green", s=20, zorder=10)
        # Plot route
        plt.plot(route.x, route.y, c="red", linewidth=2.5, alpha=0.9, zorder=5)

        # Apply DNJ
        dnj = DNJ(vf, time_step=time_step, optimize_for="time")
        # Apply DNJ in loop
        num_iter = max(1, num_iter // 5)
        for n in range(5):
            dnj.optimize_route(route, num_iter=num_iter)
            s = 2 if n == 4 else 1
            c = "black" if n == 4 else "grey"
            alpha = 0.9 if n == 4 else 0.6
            plt.plot(route.x, route.y, c=c, linewidth=s, alpha=alpha, zorder=5)
        route.recompute_times(dict_run["vel"], vf, interp=False)

        plt.tight_layout()
        plt.savefig(path_out / (name.lower().replace(" ", "_") + ".png"))
        plt.close()


if __name__ == "__main__":
    typer.run(main)
