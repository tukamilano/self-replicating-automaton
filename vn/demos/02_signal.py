"""段階2デモ (1): 29状態CAの部品 — 信号・分岐・AND・破壊と修復・発振器.

    python vn/demos/02_signal.py              # ターミナルでアニメーション
    python vn/demos/02_signal.py --gif out/signal.gif
"""
from _common import parser

from vn.ca.construct import Feeder, feeders, place
from vn.ca.grid import Grid
from vn.ca.render import LEGEND, animate, play_terminal, setup_japanese_font
from vn.ca.states import N, St

SCENES = """
 ① 分岐: 合流 C は受けた信号を、自分を指していない隣すべてへ出す (2ステップ遅延)
 ② AND : 合流 C は指してくる通常伝達が「全部」信号を運んでいる時だけ通す
         上の入力 ■□■■ と下の入力 ■■□■ → 出力 ■□□■ (3発)
 ③ 破壊と修復: 特殊伝達 ⇑ の信号が通常伝達を U に戻して線を切る。
         次に来た1発の信号は U に入って「1 0 0 0 0」= → を建て、線が直る
 ④ 発振器: 通常伝達のループ + 合流の出口 = 周期的にパルスを出す時計
 (線の終端の C は信号を吸収する「受け皿」。無いと線の先で構築が始まってしまう)
"""


def build() -> tuple[Grid, object]:
    g = Grid((20, 12))
    place(g, """
>>>>C>>>>C
....v.....
....C.....
""", (0, 0))
    place(g, """
>>>>C>>>>C
....^.....
....^.....
....^.....
""", (4, 0))
    place(g, """
>>>>>>>>>C
.....N....
.....N....
""", (10, 0))
    place(g, """
>>>v......
^..v......
^<<C>>>>>C
""", (15, 0))
    g[15, 0] = St.OE_x                     # 発振器のループに信号を1発入れておく
    drive = feeders(
        Feeder((0, 0), "1010001"),                                   # ①
        Feeder((4, 0), "1000100010001000"),                          # ② 上 (横)
        Feeder((7, 4), "0100010000000100", d=N),                     # ② 下 (縦, 1セル近い分1遅らせる)
        Feeder((10, 0), "1" + "0" * 15 + "1"),                       # ③ 通常の信号
        Feeder((12, 5), "1", d=N, kind="X", start=8),                # ③ 破壊信号
    )
    return g, drive


def main() -> None:
    args = parser(__doc__).parse_args()
    g, drive = build()
    region = (0, 18, 0, 11)
    if args.gif or args.mpl:
        setup_japanese_font()
        animate(g, region, frames=45, before_step=drive, save=args.gif, interval=250,
                title="29状態CAの部品")
        if args.gif:
            print(f"保存しました: {args.gif}")
        return
    print(SCENES)
    play_terminal(g, region, steps=45, delay=args.delay, color=not args.no_color,
                  before_step=drive, caption=lambda _: "\n" + LEGEND)
    print(SCENES)


if __name__ == "__main__":
    main()
