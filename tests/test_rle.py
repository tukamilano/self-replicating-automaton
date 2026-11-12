from pathlib import Path

import numpy as np
import pytest

from vn.ca.rle import parse_rle, to_rle

PAT = Path(__file__).parents[1] / "patterns"


def test_roundtrip_all_states():
    a = np.arange(29, dtype=np.uint8).reshape(1, 29).repeat(3, axis=0)
    a[1] = a[1][::-1]
    a[2] = 0
    a[2, 5] = 28
    assert np.array_equal(parse_rle(to_rle(a)).cells, a)


def test_parse_symbols():
    p = parse_rle("x = 4, y = 2, rule = JvN29\n.2I$pA3.!")
    assert p.rule == "JvN29"
    assert p.cells.tolist() == [[0, 9, 9, 0], [25, 0, 0, 0]]


@pytest.mark.skipif(not (PAT / "small-JvN-self-replicator.rle").exists(),
                    reason="scripts/fetch_patterns.sh 未実行")
def test_load_replicator():
    text = (PAT / "small-JvN-self-replicator.rle").read_text()
    p = parse_rle(text)
    assert p.cells.shape == (21, 12314) and p.rule == "JvN29"
    assert np.array_equal(parse_rle(to_rle(p.cells)).cells, p.cells)
