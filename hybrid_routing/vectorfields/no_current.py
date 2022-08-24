from hybrid_routing.vectorfields.base import Vectorfield
import jax.numpy as jnp


class NoCurrent(Vectorfield):
    """Circular vector field, implements Vectorfield class.
    Vectorfield defined by:
    W: (x, y) -> (u, v), u(x, y) = 0, v(x, y) = 0.
    with:
        du/dx = 0,  du/dy = 0
        dv/dx = 0,  dv/dy = 0
    """

    def __init__(self):
        pass

    def dvdx(self, x: float, y: float) -> float:
        return 0

    def dvdy(self, x: float, y: float) -> float:
        return 0

    def dudx(self, x: float, y: float) -> float:
        return 0

    def dudy(self, x: float, y: float) -> float:
        return 0

    def get_current(self, x: jnp.array, y: jnp.array) -> jnp.array:
        u = jnp.full_like(x, 0.0)
        v = jnp.full_like(x, 0.0)
        return jnp.stack([u, v])
