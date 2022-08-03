from math import pi
from typing import Iterable

import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np
from hybrid_routing.jax_utils.dnj import DNJ
from hybrid_routing.jax_utils.zivp import solve_wave
from hybrid_routing.utils.distance import dist_to_dest, min_dist_to_dest
from hybrid_routing.vectorfields.base import Vectorfield
from hybrid_routing.vectorfields.constant_current import ConstantCurrent


def optimize_route(
    vectorfield: Vectorfield,
    x_start: float,
    y_start: float,
    x_end: float,
    y_end: float,
    time_max: float = 2,
    time_step: float = 0.1,
    angle_amplitude: float = 0.25,
    num_angles: int = 50,
    vel: float = 5,
    dist_min: float = 2.0,
) -> Iterable[Iterable[float]]:

    """
    System of ODE is from Zermelo's Navigation Problem https://en.wikipedia.org/wiki/Zermelo%27s_navigation_problem#General_solution)
    1) This function first computes the locally optimized paths with Scipy's ODE solver.
    Given the starting coordinates (x_start, y_start), time (t_max), speed of the ship (vel),
    and the direction the ship points in (angle_amplitude / num_angles), the ODE solver returns
    a list of points on the locally optimized path.
    2) We then use a loop to compute all locally optimal paths with given angles in the
    angle amplitude and store them in a list.
    3) We next finds the list of paths with an end point (x1, y1) that has the smallest
    Euclidean distance to the destination (x_end, y_end).
    4) We then use the end point (x1, y1) on that path to compute the next set of paths
    by repeating the above algorithm.
    5) This function terminates till the last end point is within a neighbourhood of the
    destination (defaults 3 * vel / 4).

    Parameters
    ----------
    vectorfield : Vectorfield
        Background vectorfield for the ship to set sail on
    x_start : float
        x-coordinate of the starting position
    y_start : float
        y-coordinate of the starting position
    x_end : float
        x-coordinate of the destinating position
    y_end : float
        y-coordinate of the destinating position
    time_max : float, optional
        The total amount of time the ship is allowed to travel by at each iteration,
        by default 2
    time_step : float, optional
        Number of steps to reach from 0 to time_max (equivalently, how "smooth" each path is),
        by default 0.1
    angle_amplitude : float, optional
        The search cone range in radians, by default 0.25
    num_angles : int, optional
        Number of initial search angles, by default 50
    vel : float, optional
        Speed of the ship (unit unknown), by default 5
    dist_min : float, optional
        Minimum terminating distance around the destination (x_end, y_end), by default 2


    Yields
    ------
    Iterator[list[float]]
        Returns a list with all paths generated within the search cone.
        The path that terminates closest to destination is on top.
    """
    # Compute angle between first and last point
    dx = x_end - x_start
    dy = y_end - y_start
    cone_center = np.arctan2(dy, dx)

    # Position now
    x = x_start
    y = y_start

    while dist_to_dest((x, y), (x_end, y_end)) > dist_min:

        list_routes = solve_wave(
            vectorfield,
            x,
            y,
            time_max=time_max,
            time_step=time_step,
            cone_center=cone_center,
            angle_amplitude=angle_amplitude,
            num_angles=num_angles,
            vel=vel,
        )

        for pt in list_routes:
            plt.plot(pt[:, 0], pt[:, 1], c="gray")

        x_old, y_old = x, y
        idx_best = min_dist_to_dest(list_routes, (x_end, y_end))
        x, y, theta = list_routes[idx_best][-1]

        # Recompute the cone center
        dx = x_end - x
        dy = y_end - y
        cone_center = np.arctan2(dy, dx)

        # Move best route to first position
        list_routes.insert(0, list_routes.pop(idx_best))
        yield list_routes

        if x == x_old and y == y_old:
            break


def main():
    vectorfield = ConstantCurrent()
    dnj = DNJ(vectorfield)
    x_start, y_start = 0, 0
    x_end, y_end = 100, 100
    time_max = 2
    angle_amplitude = pi / 2
    num_angles = 10
    vel = 1

    pts = jnp.array([[x_start, y_start]])
    t_total = 0

    for list_routes in optimize_route(
        vectorfield,
        x_start,
        y_start,
        x_end,
        y_end,
        time_max=time_max,
        angle_amplitude=angle_amplitude,
        num_angles=num_angles,
        vel=vel,
    ):
        route = list_routes[0]
        print("Scipy done! Last point:", route[-1])
        pts = jnp.concatenate([pts, jnp.array(route[:, :2])])

        t_total += time_max
    print("Number of points:", pts.shape[0])
    print("Start iteration...")
    for iteration in range(200):
        pts = dnj.optimize_distance(pts)
        if iteration % 10 == 0:
            print("Iteration:", iteration)

    print("Number of points:", pts.shape[0])


if __name__ == "__main__":
    main()
