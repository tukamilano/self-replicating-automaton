"""29 状態 CA の格子エンジン.

更新規則 rules.signal_from / rules.next_state を表にして numpy で一括適用する。

高速化 (活動セル方式):
  セル x の時刻 t+1 の状態は「x と4隣の時刻 t の状態」だけで決まる。
  もし x と4隣がどれも t-1→t で変化していなければ、x(t+1) = x(t)。
  そこで「前ステップで変化したセルとその4隣」だけを再計算する。
  これはどんな決定的 CA でも厳密に正しい (近似ではない)。

格子の外側は U (地) とみなし、パターンが端に近づくと自動で配列を広げる。
座標は (行, 列) で、行は下 (南) に向かって増える。外部座標は最初の配置の
左上を (0, 0) に固定し、配列が広がっても変わらない。
"""
from __future__ import annotations

import numpy as np

from .rules import N_FLAGS, next_state, signal_from
from .states import E, N, N_STATES, S, W


def _build_tables() -> tuple[np.ndarray, np.ndarray]:
    sig = np.zeros((4, N_STATES, N_STATES), dtype=np.uint8)
    for d in (E, N, W, S):
        for me in range(N_STATES):
            for nb in range(N_STATES):
                sig[d, me, nb] = signal_from(me, nb, d)
    nxt = np.zeros((N_STATES, N_FLAGS), dtype=np.uint8)
    for me in range(N_STATES):
        for f in range(N_FLAGS):
            nxt[me, f] = next_state(me, f)
    return sig, nxt


# SIG[d, me, nb] = 方向 d の隣 nb が me に送るフラグ / NEXT[me, flags] = 次状態
SIG, NEXT = _build_tables()
_SIG_N, _SIG_E, _SIG_S, _SIG_W = (SIG[d].ravel() for d in (N, E, S, W))
_NEXT = NEXT.ravel()

MARGIN = 4   # 端からこの距離以内に変化が来たら配列を広げる
GROW = 64    # 1回に広げる幅


class Grid:
    def __init__(self, cells: np.ndarray | tuple[int, int]):
        if isinstance(cells, tuple):
            cells = np.zeros(cells, dtype=np.uint8)
        self.a = np.pad(np.asarray(cells, dtype=np.uint8), GROW)
        self.origin = np.array([GROW, GROW])     # 外部座標 (0,0) の配列内位置
        self.generation = 0
        self._changed = np.flatnonzero(self.a)   # 最初は非 U セルを全部「変化した」扱い

    # --- 読み書き ---------------------------------------------------------
    def __getitem__(self, rc: tuple[int, int]) -> int:
        r, c = self._to_array(*rc)
        h, w = self.a.shape
        return int(self.a[r, c]) if 0 <= r < h and 0 <= c < w else 0

    def __setitem__(self, rc: tuple[int, int], value: int) -> None:
        """外部から1セルを書き換える (信号の注入などに使う)。"""
        self._make_room(*self._to_array(*rc))
        r, c = self._to_array(*rc)
        self.a[r, c] = value
        self._changed = np.append(self._changed, r * self.a.shape[1] + c)

    def view(self, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
        """外部座標の範囲 [r0,r1) × [c0,c1) の写し (範囲外は U)。"""
        out = np.zeros((r1 - r0, c1 - c0), dtype=np.uint8)
        ar0, ac0 = self._to_array(r0, c0)
        h, w = self.a.shape
        sr0, sc0 = max(ar0, 0), max(ac0, 0)
        sr1, sc1 = min(ar0 + r1 - r0, h), min(ac0 + c1 - c0, w)
        if sr0 < sr1 and sc0 < sc1:
            out[sr0 - ar0:sr1 - ar0, sc0 - ac0:sc1 - ac0] = self.a[sr0:sr1, sc0:sc1]
        return out

    def bbox(self) -> tuple[int, int, int, int] | None:
        """非 U セルを囲む外部座標の範囲 (r0, r1, c0, c1)。"""
        rows = np.flatnonzero(self.a.any(axis=1))
        if len(rows) == 0:
            return None
        cols = np.flatnonzero(self.a.any(axis=0))
        o = self.origin
        return rows[0] - o[0], rows[-1] + 1 - o[0], cols[0] - o[1], cols[-1] + 1 - o[1]

    def population(self) -> int:
        return int(np.count_nonzero(self.a))

    @property
    def active(self) -> int:
        """直前のステップで変化したセル数。"""
        return len(self._changed)

    # --- 更新 -------------------------------------------------------------
    def step(self, n: int = 1) -> None:
        for _ in range(n):
            self._step()

    def _step(self) -> None:
        self.generation += 1
        ch = self._changed
        if len(ch) == 0:
            return
        a = self.a.ravel()
        w = self.a.shape[1]
        # 再計算するセル = 変化したセル + その4隣
        cand = np.unique(np.concatenate((ch, ch - 1, ch + 1, ch - w, ch + w)))
        old = a[cand]
        me = old.astype(np.intp) * N_STATES
        flags = (_SIG_N[me + a[cand - w]] | _SIG_S[me + a[cand + w]]
                 | _SIG_E[me + a[cand + 1]] | _SIG_W[me + a[cand - 1]])
        new = _NEXT[old.astype(np.intp) * N_FLAGS + flags]
        diff = new != old
        ch = cand[diff]
        a[ch] = new[diff]
        self._changed = ch
        if len(ch):
            rows, cols = np.divmod(ch, w)               # ch は昇順 → rows[0] が最小行
            self._make_room(rows[0], cols.min())
            self._make_room(rows[-1], cols.max())

    # --- 内部 -------------------------------------------------------------
    def _to_array(self, r: int, c: int) -> tuple[int, int]:
        return int(r + self.origin[0]), int(c + self.origin[1])

    def _make_room(self, r: int, c: int) -> None:
        """配列座標 (r, c) の周囲 MARGIN 以内が配列に収まるよう広げる。"""
        h, w = self.a.shape

        def need(lo_gap: int) -> int:
            return 0 if lo_gap >= MARGIN else -(-(MARGIN - lo_gap) // GROW) * GROW

        top, left = need(r), need(c)
        bottom, right = need(h - 1 - r), need(w - 1 - c)
        if not (top or bottom or left or right):
            return
        rr, cc = np.divmod(self._changed, w)
        self.a = np.pad(self.a, ((top, bottom), (left, right)))
        self.origin += (top, left)
        self._changed = (rr + top) * self.a.shape[1] + (cc + left)
