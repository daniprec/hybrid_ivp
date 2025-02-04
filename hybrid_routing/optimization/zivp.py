from typing import List

import jax.numpy as jnp
from jax.experimental.ode import odeint

# from scipy.integrate import odeint
from hybrid_routing.optimization.route import Route
from hybrid_routing.vectorfields.base import Vectorfield


def solve_ode_zermelo(
    vectorfield: Vectorfield,
    x: jnp.array,
    y: jnp.array,
    thetas: jnp.array,
    time_start: float = 0,
    time_end: float = 2,
    time_step: float = 0.1,
    vel: float = 2.0,
) -> List[Route]:
    """This function first computes the locally optimized paths with Scipy's ODE solver.
    Given the starting coordinates (x_start, y_start), time (t_max), speed of the ship
    (vel), and the direction the ship points in (angle_amplitude / num_angles),
    the ODE solver returns a list of points on the locally optimized path.

    Parameters
    ----------
    vectorfield : Vectorfield
        Background vectorfield for the ship to set sail on
    x : jnp.array
        x-coordinate of the starting positions
    y : jnp.array
        y-coordinate of the starting positions
    thetas : jnp.array
        Heading of the route (angle) in radians
    time_start : float, optional
        Start time of the iteration, by default 0
    time_end : float, optional
        End time of the iteration, by default 2
    time_step : float, optional
        Number of steps to reach from 0 to time_iter
        (equivalently, how "smooth" each path is), by default 0.1
    vel : float, optional
        Speed of the ship (unit unknown), by default 2

    Returns
    -------
    List[Route]
        Returns a list with all paths generated within the search cone.
    """
    # Define the time steps
    t = jnp.arange(time_start, time_end + time_step, time_step)

    list_routes: List[Route] = [None] * len(thetas)
    for idx, theta in enumerate(thetas):
        p = [x[idx], y[idx], theta]
        sol = odeint(vectorfield.ode_zermelo, p, t, vel)
        list_routes[idx] = Route(
            x=sol[0].astype(float),
            y=sol[1].astype(float),
            t=t,
            theta=sol[2],
            geometry=vectorfield.geometry,
        )

    return list_routes


def solve_discretized_zermelo(
    vectorfield: Vectorfield,
    x: jnp.array,
    y: jnp.array,
    thetas: jnp.array,
    time_start: float = 0,
    time_end: float = 2,
    time_step: float = 0.1,
    vel: float = 0.5,
) -> List[Route]:
    """his function instead of using the Scipy's ODE solver, we take advantage of the
    discretized vectorfield.

    Parameters
    ----------
    vectorfield : Vectorfield
        The vectorfield (background waves) for the ship to sail on
    x : jnp.array
        x-coordinate of the starting positions
    y : jnp.array
        y-coordinate of the starting positions
    thetas : jnp.array
        Heading of the route (angle) in radians
    time_end : float, optional
        The total time for the ship to travel at each iteration, by default 2
    time_step : float, optional
        The "smoothness" of the path at each local iteration, by default 0.1
    vel : float, optional
        velocity of the vessel, by default 0.5

    Returns
    -------
    List[Route]
        Returns a list of all paths thats generated at each cone search.
        All points of the paths are of Route object.
    """

    t = jnp.arange(time_start, time_end + time_step, time_step)
    list_routes: List[Route] = [None] * len(thetas)

    for idx, theta in enumerate(thetas):
        # Initialize list of (x, y) coordinates
        list_x, list_y = [x[idx]] * len(t), [y[idx]] * len(t)
        list_theta = [theta] * len(t)
        # (x, y) points will be updated during the iteration
        x_temp, y_temp = x[idx], y[idx]
        # Compute the vessel velocity components
        v_x = vel * jnp.cos(theta)
        v_y = vel * jnp.sin(theta)
        # TODO: Ensure spherical compatibility
        # Loop through the time steps
        for idx2, _ in enumerate(t):
            # Compute the displacement, affected by the vectorfield
            vf_x, vf_y = vectorfield.get_current(x_temp, y_temp)
            dx = (v_x + vf_x) * time_step
            dy = (v_y + vf_y) * time_step
            x_temp += dx
            y_temp += dy
            list_x[idx2] = x_temp
            list_y[idx2] = y_temp
        # Include the new route in the list
        list_routes[idx] = Route(
            list_x, list_y, theta=list_theta, geometry=vectorfield.geometry
        )
    return list_routes


def solve_rk_zermelo(
    vectorfield: Vectorfield,
    x: jnp.array,
    y: jnp.array,
    thetas: jnp.array,
    time_start: float = 0,
    time_end: float = 2,
    time_step: float = 0.1,
    vel: float = 2.0,
) -> List[Route]:
    """This function first computes the locally optimized paths with Runge-Kutta 4
    solver method. Given the starting coordinates (x_start, y_start), time (t_max),
    speed of the ship (vel), and the direction the ship points in
    (angle_amplitude / num_angles), the solver returns a list of points on
    the locally optimized path.

    Parameters
    ----------
    vectorfield : Vectorfield
        Background vectorfield for the ship to set sail on
    x : jnp.array
        x-coordinate of the starting positions
    y : jnp.array
        y-coordinate of the starting positions
    thetas : jnp.array
        Heading of the route (angle) in radians
    time_start : float, optional
        Start time of the iteration, by default 0
    time_end : float, optional
        End time of the iteration, by default 2
    time_step : float, optional
        Number of steps to reach from 0 to time_iter
        (equivalently, how "smooth" each path is), by default 0.1
    vel : float, optional
        Speed of the ship (unit unknown), by default 2

    Returns
    -------
    List[Route]
        Returns a list with all paths generated within the search cone.
    """
    # Define the time steps
    arr_t = jnp.arange(time_start, time_end + time_step, time_step)

    # Initializes the arrays containing the coordinates
    arr_q = [jnp.stack((x, y, thetas))] * len(arr_t)
    # Update the coordinates following the RK algorithm
    for idx, t0 in enumerate(arr_t[:-1]):
        q0 = arr_q[idx]
        k1 = jnp.asarray(vectorfield.ode_zermelo(q0, t0, vel=vel))
        k2 = jnp.asarray(
            vectorfield.ode_zermelo(
                q0 + k1 * time_step / 2, t0 + time_step / 2, vel=vel
            )
        )
        k3 = jnp.asarray(
            vectorfield.ode_zermelo(
                q0 + k2 * time_step / 2, t0 + time_step / 2, vel=vel
            )
        )
        k4 = jnp.asarray(
            vectorfield.ode_zermelo(q0 + k3 * time_step, t0 + time_step, vel=vel)
        )
        q1 = q0 + time_step * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        arr_q[idx + 1] = q1

    # Shape is (num_time_steps, 3, num_angles) where 3 = (x, y, theta)
    arr_q = jnp.asarray(arr_q)
    # Initialize list of routes and store one route per theta
    list_routes: List[Route] = [None] * len(x)
    for idx in range(len(x)):
        list_routes[idx] = Route(
            x=[v[idx] for v in arr_q[:, 0, :]],
            y=[v[idx] for v in arr_q[:, 1, :]],
            t=arr_t,
            theta=[v[idx] for v in arr_q[:, 2, :]],
            geometry=vectorfield.geometry,
        )

    return list_routes
