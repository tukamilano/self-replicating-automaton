"""段階2デモ (2): 構築アーム — テープ φ (ビット列) から何もない空間に構造物を建てる.

    python vn/demos/03_construct_arm.py                 # ターミナル
    python vn/demos/03_construct_arm.py --gif out/arm.gif

第1部: 9種の構築符号。それぞれのビット列で U から 9 種類の状態が生まれる。
第2部: テープ φ に従ってアームの先端が伸び・曲がり、閉じたループを建てる。
       できたループにデータを流すと、ループはそれを永久に保持する「記憶」になる。
       (Golly の small-JvN-self-replicator のテープも、このような信号ループ)

段階1との対応:  φ = テープのビット列 / A = 「U + 信号 → 状態」という構築規則と
アーム / 構築される X = ループ。ここでは φ を読む装置は Python (Feeder) が代役。
"""
from _common import parser

from vn.ca.construct import CODES, Feeder, feeders, path_tape, place
from vn.ca.grid import Grid
from vn.ca.render import LEGEND, animate, play_terminal, setup_japanese_font
from vn.ca.states import St, glyph

LOOP_PATH = "EEEENNNWWWWSSS"     # 作るセルの向きの列 (先端が順に曲がっていく)
DATA = "1011001"                 # ループに書き込むデータ


def part1() -> tuple[Grid, object, tuple[int, int, int, int]]:
    g = Grid((18, 8))
    fs = []
    for i, (state, code) in enumerate(CODES.items()):
        place(g, ">>>>", (2 * i, 0))
        fs.append(Feeder((2 * i, 0), code))
    return g, feeders(*fs), (0, 17, 0, 6)


def part2() -> tuple[Grid, object, tuple[int, int, int, int], str]:
    g = Grid((10, 8))
    place(g, ">", (8, 0))
    tape = path_tape(LOOP_PATH)
    gap = "0" * 20
    return g, Feeder((8, 0), tape + gap + DATA), (3, 10, 0, 8), tape


def main() -> None:
    args = parser(__doc__).parse_args()
    g1, d1, r1 = part1()
    g2, d2, r2, tape = part2()
    steps2 = len(tape) + 20 + len(DATA) + 60

    if args.gif or args.mpl:
        setup_japanese_font()
        base = args.gif[:-4] if args.gif else None
        animate(g1, r1, frames=14, before_step=d1, interval=300, title="9種の構築符号",
                save=f"{base}-codes.gif" if base else None)
        animate(g2, r2, frames=steps2 // 2, every=2, before_step=d2, interval=120,
                title="テープからループを構築", save=f"{base}-loop.gif" if base else None)
        if base:
            print(f"保存しました: {base}-codes.gif, {base}-loop.gif")
        return

    color = not args.no_color
    print(__doc__)
    input("Enter で第1部 (9種の構築符号) を開始…")
    labels = "\n".join(f"  {2*i:2d}行目: {code:<5} → {glyph(s)} ({St(s).name})"
                       for i, (s, code) in enumerate(CODES.items()))
    play_terminal(g1, r1, steps=12, delay=args.delay * 3, color=color, before_step=d1,
                  caption=lambda _: f"\n{LEGEND}\n{labels}")

    input("\nEnter で第2部 (テープからループを構築) を開始…")
    print(f"テープ φ ({len(tape)} ビット) = {tape}\n続けてデータ {DATA} を流す")

    def caption(g):
        t = g.generation
        phase = ("構築中" if t < len(tape) + 25 else "データ書き込み" if t < len(tape) + 50
                 else "ループが記憶を保持 (外部入力なし)")
        return f"[{phase}]  φ の読み出し位置 {min(t, len(tape))}/{len(tape)}\n{LEGEND}"

    play_terminal(g2, r2, steps=steps2, delay=args.delay / 2, color=color,
                  before_step=d2, caption=caption)


if __name__ == "__main__":
    main()
