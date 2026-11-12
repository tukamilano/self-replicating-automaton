"""フォン・ノイマン 29 状態セルオートマトンの状態.

番号は Golly の JvN29 規則と同じにしてある (RLE パターンをそのまま読めるように)。

  0        U       地 (ground, 何もない)
  1..8     S*      感受状態 (sensitized): 構築途中。入力ビットを1つずつ受け取って分岐する
  9..12    O→↑←↓   通常伝達 (ordinary transmission) 静止
  13..16   O→↑←↓*  通常伝達 励起 (信号を運んでいる)
  17..20   X→↑←↓   特殊伝達 (special transmission) 静止
  21..24   X→↑←↓*  特殊伝達 励起
  25..28   Cxy     合流状態 (confluent)。x=今出力中か, y=次ステップで出力するか

方向は Golly と同じく 0=東(右) 1=北(上) 2=西(左) 3=南(下)。
格子は [行, 列] で、行は下向きに増える (北 = 行 - 1)。
"""
from __future__ import annotations

from enum import IntEnum

E, N, W, S = 0, 1, 2, 3
DIR_NAMES = "ENWS"
OPPOSITE = (W, S, E, N)
# [行, 列] での変位
OFFSET = {E: (0, 1), N: (-1, 0), W: (0, -1), S: (1, 0)}
ARROW = "→↑←↓"


class St(IntEnum):
    U = 0
    # 感受状態: 名前の 0/1 はこれまでに受け取ったビット列 (先頭の1を除く)
    S = 1
    S0 = 2
    S1 = 3
    S00 = 4
    S01 = 5
    S10 = 6
    S11 = 7
    S000 = 8
    # 通常伝達 (Ordinary)
    OE = 9
    ON = 10
    OW = 11
    OS = 12
    OE_x = 13
    ON_x = 14
    OW_x = 15
    OS_x = 16
    # 特殊伝達 (Special)
    XE = 17
    XN = 18
    XW = 19
    XS = 20
    XE_x = 21
    XN_x = 22
    XW_x = 23
    XS_x = 24
    # 合流 C{今出力中}{次に出力}
    C00 = 25
    C01 = 26
    C10 = 27
    C11 = 28


N_STATES = 29

SENSITIZED = frozenset(range(1, 9))


def is_ground(s: int) -> bool:
    return s == St.U


def is_sensitized(s: int) -> bool:
    return 1 <= s <= 8


def is_ordinary(s: int) -> bool:
    return 9 <= s <= 16


def is_special(s: int) -> bool:
    return 17 <= s <= 24


def is_transmission(s: int) -> bool:
    return 9 <= s <= 24


def is_confluent(s: int) -> bool:
    return 25 <= s <= 28


def direction(s: int) -> int:
    """伝達状態が指す向き。"""
    assert is_transmission(s)
    return (s - 9) % 4


def is_excited(s: int) -> bool:
    """伝達状態が信号を運んでいる / 合流状態が今出力している。"""
    if is_transmission(s):
        return (s - 9) % 8 >= 4
    if is_confluent(s):
        return s in (St.C10, St.C11)
    return False


def ordinary(d: int, excited: bool = False) -> St:
    return St(9 + d + (4 if excited else 0))


def special(d: int, excited: bool = False) -> St:
    return St(17 + d + (4 if excited else 0))


def with_excitation(s: int, excited: bool) -> St:
    """伝達状態の向き・種類はそのままに励起/静止を切り替える。"""
    maker = ordinary if is_ordinary(s) else special
    return maker(direction(s), excited)


def confluent(now: int, nxt: int) -> St:
    return St(25 + 2 * now + nxt)


def confluent_next_bit(s: int) -> int:
    """合流状態が次のステップで出力する予定か (遅延線の2段目)。"""
    return 1 if s in (St.C01, St.C11) else 0


# 感受状態の遷移: (状態, 入力ビット) → 次状態。末端で 9 種の構築結果に分岐する
SENSITIZED_NEXT: dict[tuple[int, int], St] = {
    (St.S, 0): St.S0,    (St.S, 1): St.S1,
    (St.S0, 0): St.S00,  (St.S0, 1): St.S01,
    (St.S1, 0): St.S10,  (St.S1, 1): St.S11,
    (St.S00, 0): St.S000, (St.S00, 1): St.OW,
    (St.S01, 0): St.OS,  (St.S01, 1): St.XE,
    (St.S10, 0): St.XN,  (St.S10, 1): St.XW,
    (St.S11, 0): St.XS,  (St.S11, 1): St.C00,
    (St.S000, 0): St.OE, (St.S000, 1): St.ON,
}


def name(s: int) -> str:
    return St(s).name


# 表示用 -----------------------------------------------------------------
def glyph(s: int) -> str:
    """1文字表示。"""
    if s == St.U:
        return "·"
    if is_sensitized(s):
        return "s"
    if is_transmission(s):
        if is_ordinary(s):
            return ("▶▲◀▼" if is_excited(s) else ARROW)[direction(s)]
        return ("▷△◁▽" if is_excited(s) else "⇒⇑⇐⇓")[direction(s)]
    return "●" if is_excited(s) else "C"


# Golly の JvN 配色 (RGB)
COLORS = [
    (48, 48, 48),
    (255, 0, 0), (255, 125, 0), (255, 150, 25), (255, 175, 50),
    (255, 200, 75), (255, 225, 100), (255, 250, 125), (251, 255, 0),
    (89, 89, 255), (106, 106, 255), (122, 122, 255), (139, 139, 255),
    (27, 176, 27), (36, 200, 36), (73, 255, 73), (106, 255, 106),
    (235, 36, 36), (255, 56, 56), (255, 73, 73), (255, 89, 89),
    (185, 56, 255), (191, 73, 255), (197, 89, 255), (203, 106, 255),
    (0, 255, 128), (255, 128, 64), (255, 255, 128), (33, 215, 215),
]
