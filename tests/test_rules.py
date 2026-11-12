import itertools
import random

import pytest

from vn.ca.rules import step_cell
from vn.ca.states import N_STATES, St
from golly_ref import golly_step

R = range(N_STATES)


def test_all_single_and_pair_neighbourhoods_match_golly():
    """各セル状態 × 隣2方向までの全組合せ (残りは U) で Golly と一致。"""
    for me in R:
        for i, j in itertools.combinations(range(4), 2):
            for a in R:
                for b in R:
                    nb = [0, 0, 0, 0]
                    nb[i], nb[j] = a, b
                    assert step_cell(me, *nb) == golly_step(me, *nb), (St(me), nb)


def test_random_full_neighbourhoods_match_golly():
    rng = random.Random(0)
    for _ in range(300_000):
        me, *nb = (rng.randrange(N_STATES) for _ in range(5))
        assert step_cell(me, *nb) == golly_step(me, *nb), (St(me), nb)


@pytest.mark.parametrize("code,expected", [
    ("10000", St.OE), ("10001", St.ON), ("1001", St.OW), ("1010", St.OS),
    ("1011", St.XE), ("1100", St.XN), ("1101", St.XW), ("1110", St.XS),
    ("1111", St.C00),
])
def test_construction_codes(code, expected):
    """U に入力ビット列を順に与えると 9 種の状態が作れる。"""
    s = St.U
    for b in code:
        w = St.OE_x if b == "1" else St.OE   # 西隣から東向きの通常伝達で入力
        s = step_cell(s, St.U, St.U, St.U, w)
    assert s == expected
