"""段階3デモ: 本物の自己複製機を自作エンジンで動かす.

パターン: Golly 同梱 small-JvN-self-replicator.rle (Redstoneboi 2018, JvN29 規則)
  12314×21 セル。周期 221693 世代で自分の完全な複製を1つ作る。
  先に scripts/fetch_patterns.sh で取得しておくこと。

    python vn/demos/04_load_replicator.py --watch          # 機械部分をターミナルで観察
    python vn/demos/04_load_replicator.py                  # 1周期 (約22万世代) 完走して複製を確認
    python vn/demos/04_load_replicator.py --gens 20000     # 途中まで

構造 (段階1との対応):
  * 下端2行 = 長い信号ループ (テープ φ)。東向きの行と西向きの行がつながった環で、
    構築命令がビット列として周回している。
  * 左端の機械部分 = テープの信号を構築アームへ送る制御 (C) とアーム (A の手先)。
    構築アームは上に伸びていき、そこで子を組み立てる。
  * テープは周回するので、同じ命令列を「解釈して構築に使う」のと「子のテープとして
    書き写す」の両方ができる (A と B の役割)。
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from _common import ROOT, parser

from vn.ca.grid import Grid
from vn.ca.render import LEGEND, overview, play_terminal, save_png, to_rgb
from vn.ca.rle import load_rle, to_rle
from vn.ca.states import N_STATES, St, is_confluent, is_transmission, with_excitation

PATTERN = ROOT / "patterns" / "small-JvN-self-replicator.rle"
PERIOD = 221_693


def _structure(a: np.ndarray) -> np.ndarray:
    """信号の有無を消した「構造」: 伝達セルは静止状態に、合流セルは C00 にそろえる。"""
    q = np.arange(N_STATES, dtype=np.uint8)
    for st in range(N_STATES):
        if is_transmission(st):
            q[st] = with_excitation(st, False)
        elif is_confluent(st):
            q[st] = St.C00
    return q[a]


def find_copies(g: Grid, orig: np.ndarray, tol: float = 0.002) -> list[dict]:
    """格子中で orig と構造が一致する場所を探す.

    orig の非 U セルについて「構造 (セルの種類と向き)」と「信号 (励起・合流の位相)」を
    別々に比べる。他の個体のテープが矩形に重なることがあるので、orig が U の場所は比べない。
    """
    r0, r1, c0, c1 = g.bbox()
    world = g.view(r0, r1, c0, c1)
    ws, os_ = _structure(world), _structure(orig)
    h, w = orig.shape
    occ = orig > 0
    n_occ = int(occ.sum())
    keys = [tuple(k) for k in np.argwhere(occ)[:: max(1, n_occ // 40)]]
    kr, kc = keys[0]
    hits = []
    for r, c in np.argwhere(ws == os_[kr, kc]) - (kr, kc):
        if r < 0 or c < 0 or r + h > world.shape[0] or c + w > world.shape[1]:
            continue
        if sum(ws[r + a, c + b] != os_[a, b] for a, b in keys) > len(keys) * 0.2:
            continue
        win = world[r:r + h, c:c + w]
        struct = int((_structure(win)[occ] != os_[occ]).sum())
        if struct <= tol * n_occ:
            hits.append(dict(row=int(r + r0), col=int(c + c0), occupied=n_occ, struct=struct,
                             signal=int((win[occ] != orig[occ]).sum()) - struct))
    return hits


def snapshot(g: Grid, outdir: Path, region_head: tuple[int, int, int, int]) -> None:
    r0, r1, c0, c1 = g.bbox()
    full = g.view(r0, r1, c0, c1)
    ov = overview(full, bin_cols=max(1, (c1 - c0) // 1200))
    save_png(ov, str(outdir / f"overview_{g.generation:07d}.png"), scale=2)
    save_png(g.view(*region_head), str(outdir / f"head_{g.generation:07d}.png"), scale=4)


def main() -> None:
    p = parser(__doc__)
    p.add_argument("--gens", type=int, default=PERIOD, help="何世代回すか")
    p.add_argument("--snap-every", type=int, default=20_000)
    p.add_argument("--watch", action="store_true", help="機械部分をターミナルで観察")
    p.add_argument("--out", default=str(ROOT / "out" / "replicator"))
    args = p.parse_args()

    if not PATTERN.exists():
        raise SystemExit("パターンがありません。先に scripts/fetch_patterns.sh を実行してください")
    pat = load_rle(PATTERN)
    orig = pat.cells
    g = Grid(orig.copy())
    print(f"{PATTERN.name}: {orig.shape[1]}×{orig.shape[0]} セル, 規則 {pat.rule}")

    if args.watch:
        region = (-22, 21, 0, 110)
        play_terminal(g, region, steps=args.gens if args.gens != PERIOD else 3000,
                      every=1, delay=args.delay / 3, color=not args.no_color,
                      caption=lambda gg: f"(左端 110 列のみ表示)\n{LEGEND}")
        return

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    head = (-40, 21, 0, 160)
    snapshot(g, outdir, head)
    t0 = time.time()
    while g.generation < args.gens:
        n = min(1000, args.gens - g.generation)
        g.step(n)
        el = time.time() - t0
        eta = el / g.generation * (args.gens - g.generation)
        r0, r1, c0, c1 = g.bbox()
        print(f"\r世代 {g.generation:7d}/{args.gens}  変化セル {g.active:6d}  "
              f"範囲 行[{r0},{r1}) 列[{c0},{c1})  経過 {el:5.0f}s 残り {eta:5.0f}s",
              end="", flush=True)
        if g.generation % args.snap_every == 0:
            snapshot(g, outdir, head)
    print()
    snapshot(g, outdir, head)
    r0, r1, c0, c1 = g.bbox()
    (outdir / f"final_{g.generation}.rle").write_text(to_rle(g.view(r0, r1, c0, c1)))

    hits = find_copies(g, orig)
    print(f"\n世代 {g.generation} で元のパターンと構造が一致する個体: {len(hits)} 個")
    for h in hits:
        who = "親 (元の位置)" if (h["row"], h["col"]) == (0, 0) else "子"
        print(f"  {who}: 左上 (行 {h['row']}, 列 {h['col']})  "
              f"占有 {h['occupied']} セル中 構造の違い {h['struct']} / 信号の位相の違い {h['signal']}")
    if len(hits) >= 2:
        print("→ 自己複製に成功: 親と、セルの種類・向きがすべて同じ子がいる。")
        print("  (信号の違いは各個体の回路やテープを流れている最中のパルス。子は既に起動している)")
    print(f"スナップショット: {outdir}")


if __name__ == "__main__":
    main()
