"""
Generate all the figures used in the paper. Methods section
"""

from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import mark_inset, zoomed_inset_axes

from hybrid_routing.optimization.dnj import DNJ
from hybrid_routing.optimization.optimize import Optimizer, compute_thetas_in_cone
from hybrid_routing.optimization.route import Route
from hybrid_routing.vectorfields import Circular

"""
Create output folder
"""

path_out: Path = Path("output")
if not path_out.exists():
    path_out.mkdir()

"""
Vectorfield and initial conditions
"""

vectorfield = Circular()

x0, y0 = 8, 8

optimizer = Optimizer(
    vectorfield,
    time_iter=4,
    time_step=0.4,
    angle_amplitude=np.pi,
    num_angles=5,
    vel=1.5,
    dist_min=0.1,
    use_rk=True,
    method="direction",
)


# Initialize figure with vectorfield
# We encapsulate this code into a function because we are reusing it later
def plot_vectorfield():
    plt.figure(figsize=(5, 5))
    optimizer.vectorfield.plot(extent=(-8, 18, -8, 18), color="grey", alpha=0.8)
    plt.gca().set_aspect("equal")
    ticks = np.arange(-5, 20, 5)
    plt.xticks(ticks)
    plt.yticks(ticks)


def write_textbox(
    p0: Tuple[float],
    vel: float,
    pn: Optional[Tuple[float]] = None,
    thetas: Optional[Tuple[float]] = None,
    highlight_first: bool = False,
) -> str:
    eq = (
        r"$W(x_1,x_2) = \left\langle \frac{x_2+1}{20}, -\frac{x_1+3}{20}\right\rangle$"
        + "\n"
        + r"$\left\langle x_1(0), x_2(0) \right\rangle = \left\langle "
        + f"{p0[0]:.0f}, {p0[1]:.0f}"
        + r"\right\rangle$"
        + "\n"
    )
    if pn:
        eq += (
            r"$\left\langle x_1(T), x_2(T) \right\rangle = \left\langle "
            + f"{pn[0]:.0f}, {pn[1]:.0f}"
            + r"\right\rangle$"
            + "\n"
        )
    eq += r"$V_{vessel}$ = " + f"{vel:.1f}"
    if thetas:
        eq += "\n" + r"$\alpha(0) = "
        thetas = [(180 * t / np.pi) for t in thetas]
        t_first = thetas[0] if highlight_first else -999
        list_thetas = []
        for t in sorted(thetas):
            if t == t_first:
                list_thetas.append(r"\mathbf{" + f"{t:.0f}" + r"}\degree")
            else:
                list_thetas.append(f"{t:.0f}" + r"\degree")
        eq += ", ".join(list_thetas) + r"$"
    return eq


"""
Run Runge-Kutta method and plot its result
"""

plot_vectorfield()

# Plot source point
plt.scatter(x0, y0, c="green", s=20, zorder=10)

# Initial conditions of each segment (only angle varies)
x = np.repeat(x0, 5)
y = np.repeat(y0, 5)
theta = np.linspace(1, 5, 5) * -np.pi / 4

# Run RK method and plot each segment
list_segments = optimizer.solve_ivp(x, y, theta, time_iter=4)
for segment in list_segments:
    x, y = segment.x, segment.y
    plt.plot(x, y, c="black", alpha=0.9, zorder=5)
    plt.scatter(x[1:-1], y[1:-1], c="orange", s=10, zorder=10)
    plt.scatter(x[-1], y[-1], c="red", s=20, zorder=10)


# Add equations
bbox = {"boxstyle": "round", "facecolor": "white", "alpha": 1}
thetas = [float(route.theta[0]) for route in list_segments]
eq_rk = write_textbox((x0, y0), optimizer.vel, thetas=thetas)
plt.text(-4.5, -5.5, eq_rk, fontsize=10, verticalalignment="bottom", bbox=bbox)

# Store plot
plt.xlim(-5, 15)
plt.ylim(-6, 12)
plt.tight_layout()
plt.savefig(path_out / "methods_runge_kutta.png")
plt.close()

print("Runge-Kutta - Finished")

"""
Exploration step
"""

x0, y0 = 12, -4
xn, yn = 4, 14
optimizer.vel = 1.5
optimizer.time_iter = 0.1
optimizer.time_step = 0.01
optimizer.angle_amplitude = np.pi / 2
optimizer.angle_heading = np.pi / 3
run = optimizer.optimize_route((x0, y0), (xn, yn))
list_routes_plot = next(run)

for list_routes in run:
    if optimizer.exploration:
        list_routes_plot = deepcopy(list_routes)
    else:
        break

plot_vectorfield()


# Plot each route segment
# We encapsulate this code into a function because we are reusing it later
def plot_routes(list_routes: List[Route]):
    # Plot source point
    plt.scatter(x0, y0, c="green", s=20, zorder=10)
    plt.scatter(xn, yn, c="green", s=20, zorder=10)
    # Plot routes
    for idx, route in enumerate(list_routes):
        x, y = route.x, route.y
        # Highlight the best route of the bunch
        s = 3 if idx == 0 else 1.5
        plt.plot(x, y, c="black", linewidth=s, alpha=0.9, zorder=5)


plot_routes(list_routes_plot)

# Compute angles
cone_center = optimizer.geometry.angle_p0_to_p1((x0, y0), (xn, yn))
arr_theta = compute_thetas_in_cone(
    cone_center, optimizer.angle_amplitude, optimizer.num_angles
)

# Plot original angles
for theta in arr_theta:
    x = x0 + np.cos(theta) * np.array([0, 10])
    y = y0 + np.sin(theta) * np.array([0, 10])
    plt.plot(x, y, linestyle="--", color="orange", alpha=1, zorder=3)

# Add equations
thetas = [route.theta[0] for route in list_routes_plot]
eq_explo = write_textbox(
    (x0, y0), optimizer.vel, pn=(xn, yn), thetas=thetas, highlight_first=True
)
plt.text(-7.5, 15.5, eq_explo, fontsize=9, verticalalignment="top", bbox=bbox)

# Store plot
plt.xlim(-8, 16)
plt.ylim(-7, 16)
plt.tight_layout()
plt.savefig(path_out / "methods_hybrid_exploration.png")
plt.close()

print("Exploration step - Finished")

"""
Exploitation step
"""

for list_routes in run:
    if not optimizer.exploration:
        list_routes_plot = deepcopy(list_routes)
    else:
        break

plot_vectorfield()
plot_routes(list_routes_plot)

# Compute angles
angle_best = list_routes_plot[0].theta[0]
arr_theta = compute_thetas_in_cone(
    angle_best, optimizer.angle_amplitude / 5, optimizer.num_angles
)

# Plot original angles
for theta in arr_theta:
    x = x0 + np.cos(theta) * np.array([0, 10])
    y = y0 + np.sin(theta) * np.array([0, 10])
    plt.plot(x, y, linestyle="--", color="orange", alpha=1, zorder=3)

# Add equations
thetas = [route.theta[0] for route in list_routes_plot]
eq_explo = write_textbox(
    (x0, y0), optimizer.vel, pn=(xn, yn), thetas=thetas, highlight_first=True
)
plt.text(-7.5, -6.5, eq_explo, fontsize=9, verticalalignment="bottom", bbox=bbox)

# Store plot
plt.xlim(-8, 16)
plt.ylim(-7, 16)
plt.tight_layout()
plt.savefig(path_out / "methods_hybrid_exploitation.png")
plt.close()

print("Exploitation step - Finished")

"""
Finish optimization
"""

for list_routes in run:
    list_routes_plot = deepcopy(list_routes)
# Append goal
route: Route = list_routes_plot[0]
route.append_point_end(p=(xn, yn), vel=optimizer.vel)

plot_vectorfield()
plot_routes([route])

# Add equations
thetas = [route.theta[0] for route in list_routes_plot]
eq_opt = write_textbox((x0, y0), optimizer.vel, pn=(xn, yn))
plt.text(-6.5, -6.5, eq_opt, fontsize=10, verticalalignment="bottom", bbox=bbox)

# Store plot
plt.xlim(-7, 16)
plt.ylim(-7, 16)
plt.tight_layout()
plt.savefig(path_out / "methods_hybrid_optimized.png")
plt.close()

print("Optimization - Finished")

"""
Discrete Newton-Jacobi
"""

dnj = DNJ(vectorfield, time_step=optimizer.time_step, optimize_for="fuel")

plot_vectorfield()
plt.scatter(route.x[0], route.y[0], c="green", s=20, zorder=10)

# Prepare zoom
fig = plt.gcf()
ax = plt.gca()
axins = zoomed_inset_axes(ax, zoom=2.5, loc="center right")
optimizer.vectorfield.plot(extent=(2, 7, 11, 16), color="grey", alpha=0.8, scale=2)

# Goal point and original route (plot both in normal and zoom)
for axis in [ax, axins]:
    axis.scatter(route.x[-1], route.y[-1], c="green", s=20, zorder=10)
    axis.plot(route.x, route.y, c="red", linewidth=2, alpha=0.9, zorder=5)

# Apply DNJ in loop
for n in range(5):
    dnj.optimize_route(route, num_iter=2000)
    s = 2 if n == 4 else 1
    c = "black" if n == 4 else "grey"
    alpha = 0.9 if n == 4 else 0.6
    # Plot both in normal and zoom
    for axis in [ax, axins]:
        axis.plot(route.x, route.y, c=c, linewidth=s, alpha=alpha, zorder=5)

# Add equations
ax.text(-6.5, -6.5, eq_opt, fontsize=10, verticalalignment="bottom", bbox=bbox)

# Limit zoom axis
axins.set_xlim(3, 6)
axins.set_ylim(12, 15)
mark_inset(ax, axins, loc1=1, loc2=3, fc="none", ec="0.5")
# Hide ticks in zoomed axis
plt.tick_params(
    axis="both",  # changes apply to the x-axis
    which="both",  # both major and minor ticks are affected
    bottom=False,  # ticks along the bottom edge are off
    top=False,  # ticks along the top edge are off
    left=False,
    right=False,
    labelbottom=False,  # labels along the bottom edge are off
    labelleft=False,
)

# Limit normal axis
ax.set_xlim(-7, 16)
ax.set_ylim(-7, 16)

# Store plot
plt.draw()
fig.tight_layout()
plt.savefig(path_out / "methods_hybrid_dnj.png")
plt.close()

print("DNJ - Finished")
