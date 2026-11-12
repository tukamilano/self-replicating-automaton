"""構築: 信号列 (ビット列) で何もない空間 U にセルを建てる.

U に信号が届くと感受状態 S になり、続くビットで分岐して 9 種のどれかになる。
これがフォン・ノイマンの「構築」の最小単位で、段階1の
「A が記述 φ を読んで部品を作る」のセル空間版にあたる。

    符号        作られる状態
    1 0 0 0 0   通常伝達 → (東)
    1 0 0 0 1   通常伝達 ↑ (北)
    1 0 0 1     通常伝達 ← (西)
    1 0 1 0     通常伝達 ↓ (南)
    1 0 1 1     特殊伝達 ⇒
    1 1 0 0     特殊伝達 ⇑
    1 1 0 1     特殊伝達 ⇐
    1 1 1 0     特殊伝達 ⇓
    1 1 1 1     合流 C
"""
from __future__ import annotations

from .states import E, N, S, W, St, ordinary, special

CODES: dict[St, str] = {
    St.OE: "10000", St.ON: "10001", St.OW: "1001", St.OS: "1010",
    St.XE: "1011", St.XN: "1100", St.XW: "1101", St.XS: "1110",
    St.C00: "1111",
}


def tape_for(states) -> str:
    """作りたい状態の列 → 構築アームに流すビット列。"""
    return "".join(CODES[St(s)] for s in states)


def path_tape(dirs: str) -> str:
    """'EENNW…' の向きの通常伝達セルを順に作る (先端が次々と曲がって伸びる)。"""
    return tape_for(ordinary("ENWS".index(d)) for d in dirs)


class Feeder:
    """外部からビット列を1ステップ1ビットずつ伝達セルに注入する (テープ読み取り機の代役).

    grid.step() の直前に毎回呼ぶ。ビット1ならそのセルを励起状態に、0なら静止状態にする。
    """

    def __init__(self, cell: tuple[int, int], bits: str, d: int = E, kind: str = "O",
                 start: int = 0):
        self.cell = cell
        self.bits = bits
        self.start = start
        maker = ordinary if kind == "O" else special
        self.quiet, self.excited = maker(d, False), maker(d, True)
        self.t = 0

    @property
    def done(self) -> bool:
        return self.t >= self.start + len(self.bits)

    def __call__(self, grid) -> None:
        i = self.t - self.start
        if 0 <= i < len(self.bits):
            grid[self.cell] = self.excited if self.bits[i] == "1" else self.quiet
        elif i == len(self.bits):
            grid[self.cell] = self.quiet
        self.t += 1


def feeders(*fs: Feeder):
    """複数の Feeder をまとめて before_step に渡す用。"""
    def call(grid):
        for f in fs:
            f(grid)
    return call


# --- ASCII レイアウト -------------------------------------------------------
#   .  地 U
#   > ^ < v  通常伝達 (静止)
#   E N W S  特殊伝達 (静止)  ※ 文字は向き
#   C        合流
_LAYOUT = {
    ".": St.U, " ": St.U,
    ">": ordinary(E), "^": ordinary(N), "<": ordinary(W), "v": ordinary(S),
    "E": special(E), "N": special(N), "W": special(W), "S": special(S),
    "C": St.C00,
}


def place(grid, text: str, at: tuple[int, int] = (0, 0)) -> None:
    """ASCII で描いた配置を grid の at (左上) に置く。"""
    lines = [ln for ln in text.strip("\n").splitlines()]
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            s = _LAYOUT[ch]
            if s != St.U:
                grid[at[0] + r, at[1] + c] = s
