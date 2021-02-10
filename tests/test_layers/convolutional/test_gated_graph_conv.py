from core import run_layer, MODES
from spektral import layers

config = {
    "layer": layers.GatedGraphConv,
    "modes": [MODES["SINGLE"], MODES["MIXED"]],
    "kwargs": {"channels": 10, "n_layers": 3},
    "dense": False,
    "sparse": True,
}


def test_layer():
    run_layer(config)