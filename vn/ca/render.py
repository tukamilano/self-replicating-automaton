"""表示: ターミナル (ANSI 色付き文字) と matplotlib (Golly 配色の画像/アニメーション)."""
from __future__ import annotations

import sys
import time
from typing import Callable

import numpy as np

from .states import COLORS, glyph, is_confluent, is_excited, is_ordinary, is_sensitized, is_special

_RGB = np.array(COLORS, dtype=np.uint8)


# --- ターミナル --------------------------------------------------------------
def _ansi(s: int) -> str:
    if s == 0:
        return "\033[90m"            # 灰
    if is_sensitized(s):
        return "\033[33m"            # 黄
    if is_ordinary(s):
        return "\033[1;92m" if is_excited(s) else "\033[94m"   # 励起=明るい緑 / 静止=青
    if is_special(s):
        return "\033[1;95m" if is_excited(s) else "\033[91m"   # 励起=紫 / 静止=赤
    if is_confluent(s):
        return "\033[1;96m" if is_excited(s) else "\033[36m"
    return ""


def ascii_art(cells: np.ndarray, color: bool = True) -> str:
    lines = []
    for row in cells:
        if color:
            lines.append("".join(_ansi(int(s)) + glyph(int(s)) for s in row) + "\033[0m")
        else:
            lines.append("".join(glyph(int(s)) for s in row))
    return "\n".join(lines)


LEGEND = ("凡例: →↑←↓ 通常伝達 (▶▲◀▼=信号あり)   ⇒⇑⇐⇓ 特殊伝達 (▷△◁▽=信号あり)\n"
          "      C 合流 (●=出力中)   s 感受状態(構築中)   · 地U")


def play_terminal(grid, region: tuple[int, int, int, int], steps: int,
                  every: int = 1, delay: float = 0.08, color: bool = True,
                  caption: Callable[[object], str] | None = None,
                  before_step: Callable[[object], None] | None = None) -> None:
    """ターミナルでアニメーション表示。before_step(grid) で毎ステップ外部入力できる。"""
    interactive = sys.stdout.isatty()
    for i in range(steps + 1):
        if i % every == 0 or i == steps:
            frame = ascii_art(grid.view(*region), color)
            text = f"世代 {grid.generation}" + (f"  {caption(grid)}" if caption else "")
            if interactive:
                sys.stdout.write("\033[H\033[2J")
            sys.stdout.write(f"{text}\n{frame}\n")
            sys.stdout.flush()
            if interactive and delay:
                time.sleep(delay)
        if i < steps:
            if before_step:
                before_step(grid)
            grid.step()


# --- 画像 --------------------------------------------------------------------
def to_rgb(cells: np.ndarray) -> np.ndarray:
    return _RGB[cells]


def save_png(cells: np.ndarray, path: str, scale: int = 4) -> None:
    import matplotlib.pyplot as plt
    img = np.kron(to_rgb(cells), np.ones((scale, scale, 1), dtype=np.uint8))
    plt.imsave(path, img)


def overview(cells: np.ndarray, bin_cols: int) -> np.ndarray:
    """横に長いパターン用の縮小図: bin_cols 列ごとに「代表状態」を1画素にする.

    励起 > 合流 > 感受 > 伝達 > U の優先度で、その区間に現れる状態を選ぶ。
    """
    h, w = cells.shape
    pad = (-w) % bin_cols
    c = np.pad(cells, ((0, 0), (0, pad))).reshape(h, -1, bin_cols)
    prio = np.zeros(29, dtype=np.int8)
    for s in range(29):
        prio[s] = (0 if s == 0 else 4 if is_excited(s) else 3 if is_confluent(s)
                   else 2 if is_sensitized(s) else 1)
    idx = prio[c].argmax(axis=2)
    return np.take_along_axis(c, idx[..., None], axis=2)[..., 0]


def animate(grid, region: tuple[int, int, int, int], frames: int, every: int = 1,
            before_step: Callable[[object], None] | None = None,
            save: str | None = None, interval: int = 80, title: str = ""):
    """matplotlib のアニメーション。save='out.gif' で GIF 保存 (表示はしない)。"""
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    fig, ax = plt.subplots(figsize=(min(12, 0.25 * (region[3] - region[2]) + 1),
                                    min(8, 0.25 * (region[1] - region[0]) + 1.2)))
    im = ax.imshow(to_rgb(grid.view(*region)), interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    label = ax.set_title(f"{title} 世代 {grid.generation}")

    def update(_):
        for _ in range(every):
            if before_step:
                before_step(grid)
            grid.step()
        im.set_data(to_rgb(grid.view(*region)))
        label.set_text(f"{title} 世代 {grid.generation}")
        return im, label

    anim = FuncAnimation(fig, update, frames=frames, interval=interval, blit=False)
    if save:
        anim.save(save, writer=PillowWriter(fps=max(1, 1000 // interval)))
        plt.close(fig)
    else:
        plt.show()
    return anim


def setup_japanese_font() -> None:
    """matplotlib のタイトルで日本語が化けないようにする (macOS の標準フォント)。"""
    import matplotlib
    from matplotlib import font_manager
    for name in ("Hiragino Sans", "Hiragino Maru Gothic Pro", "YuGothic", "Noto Sans CJK JP"):
        if any(f.name == name for f in font_manager.fontManager.ttflist):
            matplotlib.rcParams["font.family"] = name
            return
