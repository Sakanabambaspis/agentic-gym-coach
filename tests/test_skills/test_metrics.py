"""metrics — the single Epley definition shared by trend_analysis and snapshot."""

import pytest
import polars as pl

from skills.metrics import EPLEY_MAX_REPS, epley_expr, est_1rm, qualifies_for_est_1rm


def test_cap_is_the_doctrine_constant():
    assert EPLEY_MAX_REPS == 6  # "~5RM or heavier", Training ch04


def test_scalar_formula():
    assert est_1rm(100.0, 6) == pytest.approx(120.0)  # 100 * (1 + 6/30)


def test_expr_matches_scalar():
    df = pl.DataFrame({"w": [100.0, 80.0], "r": [6, 3]})
    out = df.select(epley_expr("w", "r").alias("e"))["e"][0]
    assert out == pytest.approx(est_1rm(100.0, 6))


def test_qualifier_requires_load_and_heavy_reps():
    df = pl.DataFrame({"w": [100.0, None, 100.0, 100.0], "r": [6, 6, 7, None]})
    keep = df.filter(qualifies_for_est_1rm("w", "r"))
    assert keep.height == 1  # only the loaded 6-rep set qualifies
