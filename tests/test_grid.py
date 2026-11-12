import random

import numpy as np

from vn.ca.grid import Grid
from vn.ca.states import N_STATES, St
from golly_ref import golly_step


def dense_reference_step(a: np.ndarray) -> np.ndarray:
    """格子全体を Golly 直訳の関数で素朴に1ステップ (外側は U)。"""
    p = np.pad(a, 1)
    out = np.zeros_like(a)
    for r in range(a.shape[0]):
        for c in range(a.shape[1]):
            out[r, c] = golly_step(p[r + 1, c + 1], p[r, c + 1], p[r + 1, c + 2],
                                   p[r + 2, c + 1], p[r + 1, c])
    return out


def test_active_cell_engine_matches_dense_reference():
    rng = np.random.default_rng(0)
    # 疎なランダム盤面 (U 多め) を 40 ステップ、全面計算と照合
    a = np.where(rng.random((24, 30)) < 0.5, rng.integers(0, N_STATES, (24, 30)), 0)
    a = np.pad(a.astype(np.uint8), 8)
    g = Grid(a.copy())
    ref = a.copy()
    for _ in range(40):
        g.step()
        ref = dense_reference_step(ref)
        assert np.array_equal(g.view(0, ref.shape[0], 0, ref.shape[1]), ref)


def test_signal_travels_one_cell_per_step():
    g = Grid((1, 10))
    for c in range(10):
        g[0, c] = St.OE
    g[0, 0] = St.OE_x
    for t in range(1, 9):
        g.step()
        assert [c for c in range(10) if g[0, c] == St.OE_x] == [t]


def test_grid_grows_when_construction_reaches_edge():
    # 東向きの線の先に何度も「通常伝達・東 (10000)」を作らせると線が伸び続ける
    g = Grid((1, 2))
    g[0, 0] = St.OE
    g[0, 1] = St.OE
    bits = "10000" * 80
    for b in bits:
        g[0, 0] = St.OE_x if b == "1" else St.OE
        g.step()
    g.step(100)   # 最後の符号が先端まで届くのを待つ
    r0, r1, c0, c1 = g.bbox()
    assert (r0, r1, c0) == (0, 1, 0) and c1 == 2 + 80
    assert all(g[0, c] == St.OE for c in range(1, c1))
