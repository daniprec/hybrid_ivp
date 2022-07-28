from typing import Iterable, Tuple

import numpy as np
import tensorflow as tf
from hybrid_routing.tf_utils.benchmark import background_vector_field


def wave(
    t: tf.Tensor, p: tf.Tensor, vel: tf.Tensor = tf.constant(3, dtype=tf.float32)
) -> tf.Tensor:
    x, y, theta = p

    with tf.GradientTape(persistent=True) as tape:
        tape.watch(x)
        tape.watch(y)
        x0, x1 = background_vector_field(x, y)

    dxdt = tf.math.multiply(tf.cos(theta), vel) + x0
    dydt = tf.math.multiply(tf.sin(theta), vel) + x1

    du = tape.jacobian(x0, [x, y])
    dv = tape.jacobian(x1, [x, y])
    dthetadt = (
        tf.math.multiply(dv[0], tf.math.pow(tf.sin(theta), 2))
        + tf.math.multiply(
            tf.math.multiply(tf.sin(theta), tf.cos(theta)), du[0] - dv[1]
        )
        - tf.math.multiply(du[1], tf.math.pow(tf.cos(theta), 2))
    )
    p_new = tf.convert_to_tensor([dxdt, dydt, dthetadt], dtype=tf.float32)
    return tf.constant(p_new)


def dist_to_dest(p0: Tuple, p1: Tuple) -> float:
    """Compute the distance between two points."""
    return np.sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)


def min_dist_to_dest(list_routes: Iterable[np.array], pt_goal: Tuple) -> int:
    """Out of a list of routes, returns the index of the route the ends
    at the minimum distance to the goal.

    Parameters
    ----------
    list_routes : Iterable[np.array]
        List of routes, defined by (x, y, theta)
    pt_goal : _type_
        Goal point, defined by (x, y)

    Returns
    -------
    int
        Index of the route that ends at the minimum distance to the goal.
    """
    min_dist = np.inf
    for idx, route in enumerate(list_routes):
        dist = dist_to_dest(route[-1], pt_goal)
        if dist < min_dist:
            min_dist = dist
            idx_best_point = idx
    return idx_best_point


if __name__ == "__main__":
    p = tf.constant([1.0, 1.0, 0.2], dtype=tf.float32)
    t = tf.constant(np.linspace(0, 10, 1), dtype=tf.float32)
    print(wave(t, p))