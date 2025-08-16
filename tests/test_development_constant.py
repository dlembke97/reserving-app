import os
import sys

import pandas as pd
import chainladder as cl

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from helper_functions import ReservingAppTriangle


def build_triangle():
    data = pd.DataFrame(
        {
            "origin": [2018, 2018, 2019, 2019],
            "development": [2019, 2020, 2020, 2021],
            "loss": [100, 150, 80, 120],
            "prem": [200, 200, 180, 180],
        }
    )
    return ReservingAppTriangle(
        data, origin="origin", development="development", value_cols=["loss", "prem"]
    )


def _apply_default_selected(tri, key):
    ldf_series = (
        tri.ldf_exhibit[key]
        .loc[tri.ldf_exhibit[key]["Avg Method"] == "Volume Weighted"]
        .iloc[0, 1:]
        .fillna(1.0)
        .astype(float)
    )
    tri.apply_selected_ldfs(key, ldf_series)


def test_chainladder_uses_selected_ldfs():
    tri = build_triangle()
    key = (None, "loss")
    _apply_default_selected(tri, key)
    models = tri.get_development_model("chainladder")
    pipe = models[key]["chainladder"]
    assert "selected" in pipe.named_steps
    assert isinstance(pipe.named_steps["selected"], cl.DevelopmentConstant)


def test_cape_cod_uses_selected_ldfs():
    tri = build_triangle()
    key = (None, "loss")
    _apply_default_selected(tri, key)
    models = tri.get_development_model("cape_cod", prem_col="prem")
    pipe = models[key]["cape_cod"]
    assert "selected" in pipe.named_steps
    assert isinstance(pipe.named_steps["selected"], cl.DevelopmentConstant)


def test_apply_selected_ldfs_ignores_missing_keys():
    data = pd.DataFrame(
        {
            "origin": [2018, 2018, 2019, 2019],
            "development": [2019, 2020, 2020, 2021],
            "loss": [100, 150, 80, 120],
            "prem": [200, 200, 180, 180],
        }
    )
    # First triangle with loss to obtain an LDF series
    tri_loss = ReservingAppTriangle(
        data, origin="origin", development="development", value_cols=["loss"]
    )
    key_loss = (None, "loss")
    ldf_series = (
        tri_loss.ldf_exhibit[key_loss]
        .loc[tri_loss.ldf_exhibit[key_loss]["Avg Method"] == "Volume Weighted"]
        .iloc[0, 1:]
    )

    # Second triangle excludes loss; applying with old key should be a no-op
    tri_prem = ReservingAppTriangle(
        data, origin="origin", development="development", value_cols=["prem"]
    )
    tri_prem.apply_selected_ldfs(key_loss, ldf_series)
    assert key_loss not in tri_prem.custom_ldfs

