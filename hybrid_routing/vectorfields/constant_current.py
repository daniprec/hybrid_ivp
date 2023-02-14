from functools import partial
from typing import Tuple

import jax.numpy as jnp
from jax import jit

from hybrid_routing.vectorfields.base import Vectorfield


class ConstantCurrent(Vectorfield):
    """Constant vector field, implements Vectorfield class.
    Vectorfield defined by:
    W: (x, y) -> (u, v), u(x, y) = 0.2, v(x, y) = -0.2
    with:
        du/dx = 0,      du/dy = 0
        dv/dx = 0,      dv/dy = 0
    """

    @partial(jit, static_argnums=(0,))
    def dv(self, x: jnp.array, y: jnp.array) -> Tuple[jnp.array]:
        return jnp.asarray([0]), jnp.asarray([0])

    @partial(jit, static_argnums=(0,))
    def du(self, x: jnp.array, y: jnp.array) -> Tuple[jnp.array]:
        return jnp.asarray([0]), jnp.asarray([0])

    @partial(jit, static_argnums=(0,))
    def get_current(self, x: jnp.array, y: jnp.array) -> jnp.array:
        u = jnp.tile(0.2, x.shape)
        v = jnp.tile(-0.2, x.shape)
        return jnp.stack([u, v])
