"""29 状態の遷移規則 (フォン・ノイマン近傍: 上下左右).

1セルの次状態は「自分の状態」と「4つの隣から届く入力」だけで決まる。
読みやすさのため2段に分けている:

  1. signal_from(me, nb, d) : 方向 d の隣 nb が自分 me に何を送ってくるか (フラグ)
  2. next_state(me, flags)  : 届いた入力フラグの OR から次状態を決める

格子エンジン (grid.py) はこの2つの関数を表にして numpy で一括適用する。
挙動は Golly の JvN29 実装と一致することを tests/test_rules.py で確かめている。

規則の要点
----------
* 伝達 (通常 O / 特殊 X): 自分を指している同種の励起セル、または隣の出力中の合流
  セルから入力があると、次ステップで励起する (= 1ステップ遅延で信号が進む)。
  ただし自分が指している相手からの入力 (正面衝突) は受け付けない。
* 破壊: 通常伝達の信号が特殊伝達/… に当たると逆種を U に戻す。
    O の信号 → X を破壊 / X の信号 → O と C を破壊。
* 合流 C: 指してくる通常伝達「すべて」が励起していれば (AND) 受理し、
  2ステップ後に、自分を指していない隣の伝達セルすべてへ出力する (分岐)。
* 構築: U に (O でも X でも) 信号が来ると感受状態 S になり、以後毎ステップ
  入力ビット (信号あり=1/なし=0) を1つずつ取り込んで、9種の状態のどれかになる。
"""
from __future__ import annotations

from .states import (OPPOSITE, SENSITIZED_NEXT, St, confluent,
                     confluent_next_bit, direction, is_confluent, is_excited,
                     is_ordinary, is_special, is_transmission, with_excitation)

# 入力フラグ ---------------------------------------------------------------
O_IN = 1        # 励起した通常伝達が自分を指している (正面衝突を除く)
O_IN_ANY = 2    # 同上、正面衝突も含む (破壊・構築・合流の判定用)
O_QUIET_IN = 4  # 静止した通常伝達が自分を指している (合流の AND 判定用)
X_IN = 8        # 励起した特殊伝達が自分を指している (正面衝突を除く)
X_IN_ANY = 16   # 同上、正面衝突も含む
C_IN = 32       # 隣の合流セルが出力中で、自分はそれを指していない
N_FLAGS = 64


def signal_from(me: int, nb: int, d: int) -> int:
    """自分から見て方向 d にいる隣 nb が、自分に送ってくる入力フラグ。"""
    i_point_at_it = is_transmission(me) and direction(me) == d
    if is_transmission(nb) and direction(nb) == OPPOSITE[d]:   # nb が自分を指している
        if is_ordinary(nb):
            if not is_excited(nb):
                return O_QUIET_IN
            return O_IN_ANY | (0 if i_point_at_it else O_IN)
        if is_excited(nb):
            return X_IN_ANY | (0 if i_point_at_it else X_IN)
        return 0
    if is_confluent(nb) and is_excited(nb) and not i_point_at_it:
        return C_IN
    return 0


def next_state(me: int, f: int) -> St:
    """届いた入力フラグ f (4隣の OR) から次状態を決める。"""
    # --- 地 U と 感受状態: 構築 ---
    if me == St.U or 1 <= me <= 8:
        bit = 1 if f & (O_IN_ANY | X_IN_ANY) else 0
        if me == St.U:
            return St.S if bit else St.U
        return SENSITIZED_NEXT[(me, bit)]

    # --- 合流 ---
    if is_confluent(me):
        if f & X_IN_ANY:
            return St.U                                   # 特殊伝達の信号で破壊
        accepted = bool(f & O_IN_ANY) and not (f & O_QUIET_IN)   # AND
        return confluent(confluent_next_bit(me), int(accepted))  # 遅延線を1段進める

    # --- 伝達 ---
    if is_ordinary(me) and f & X_IN_ANY:
        return St.U                                       # X の信号が O を破壊
    if is_special(me) and f & O_IN_ANY:
        return St.U                                       # O の信号が X を破壊
    same_kind = O_IN if is_ordinary(me) else X_IN
    return with_excitation(me, bool(f & (same_kind | C_IN)))


def step_cell(me: int, n: int, e: int, s: int, w: int) -> St:
    """1セル分の更新 (読む用・テスト用)。"""
    from .states import E, N, S, W
    f = (signal_from(me, n, N) | signal_from(me, e, E)
         | signal_from(me, s, S) | signal_from(me, w, W))
    return next_state(me, f)
