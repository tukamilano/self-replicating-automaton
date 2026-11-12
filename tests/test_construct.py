import pytest

from vn.ca.construct import CODES, Feeder, path_tape, place, tape_for
from vn.ca.grid import Grid
from vn.ca.states import St, is_excited


@pytest.mark.parametrize("state", list(CODES))
def test_each_code_builds_its_state_in_grid(state):
    g = Grid((1, 4))
    place(g, ">>>", (0, 0))
    f = Feeder((0, 0), CODES[state])
    for _ in range(12):
        f(g)
        g.step()
    assert g[0, 3] == state


def test_codes_are_prefix_free():
    codes = list(CODES.values())
    assert not any(a != b and b.startswith(a) for a in codes for b in codes)


def test_arm_builds_closed_loop_and_loop_stores_data():
    path = "EEEENNNWWWWSSS"
    g = Grid((10, 8))
    place(g, ">", (8, 0))
    f = Feeder((8, 0), path_tape(path) + "0" * 20 + "1011001")
    for _ in range(len(f.bits) + 5):
        f(g)
        g.step()
    # 期待されるループの形
    expected = {}
    r, c = 8, 1
    for d in path:
        expected[(r, c)] = d
        r, c = {"E": (r, c + 1), "N": (r - 1, c), "W": (r, c - 1), "S": (r + 1, c)}[d]
    assert (r, c) == (8, 1)   # 最後のセルは最初のセルを指す = 閉じている
    for (rr, cc), d in expected.items():
        assert St(g[rr, cc]).name.startswith("O" + d)
    # 外部入力を止めても、ループ内の信号パターンは周期 14 で回り続ける
    def snapshot():
        return tuple(is_excited(g[p]) for p in expected)
    s0 = snapshot()
    assert sum(s0) == 4          # "1011001" の 1 が4つ
    g.step(14)
    assert snapshot() == s0
    g.step(7)
    assert snapshot() != s0


def test_tape_for_concatenates():
    assert tape_for([St.OE, St.C00]) == "10000" + "1111"
