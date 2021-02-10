from core import run_layer, MODES
from spektral import layers

config = {
    "layer": layers.GINConv,
    "modes": [MODES["SINGLE"], MODES["MIXED"]],
    "kwargs": {"channels": 8, "activation": "relu", "mlp_hidden": [16]},
    "dense": False,
    "sparse": True,
}


def test_layer():
    run_layer(config)
    config["kwargs"]["epsilon"] = 0.
    run_layer(config)