"""段階1デモ: A+B+C+φ の論理を動かす.

    python -m vn.demos.01_logic   (または python vn/demos/01_logic.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from vn.logic.machine import (Lineage, Machine, Tape, encode, decode,  # noqa: E402
                              naive_self_description_lengths, self_reproducing)


def header(t: str) -> None:
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def show_lineage(lin: Lineage) -> None:
    for g, pop in enumerate(lin.generations):
        kinds: dict[str, int] = {}
        for m in pop:
            kinds[str(m)] = kinds.get(str(m), 0) + 1
        summary = ", ".join(f"{k} ×{v}" for k, v in kinds.items())
        print(f"  第{g}世代 ({len(pop):3d}体): {summary}")


def main() -> None:
    header("実験1: A+B+C + φ(A+B+C)  — 1回の複製を詳しく")
    parent = self_reproducing(("A", "B", "C"))
    print(f"親: {parent}\nφ = {parent.tape}")
    log: list[str] = []
    child = parent.reproduce(log)
    print("\n".join("  " + line for line in log))
    print(f"子: {child}")
    print(f"子 == 親 ? {child == parent}")

    header("実験2: 系譜 — 自己複製が続く (個体数が倍々に)")
    show_lineage(Lineage.run(parent, 4))

    header("実験3: B(複製機) を持たない A+C + φ(A+C)")
    m = self_reproducing(("A", "C"))
    log = []
    c = m.reproduce(log)
    print("\n".join("  " + line for line in log))
    print(f"子: {c}")
    print(f"孫: {c.reproduce()}  ← 子はテープを持たないので複製できない")
    print("\n  では φ にテープ自身の記述も入れたら? (B なしで済ませる試み)")
    for k, n in enumerate(naive_self_description_lengths(2, 6), 1):
        print(f"   入れ子の深さ {k}: 記述長 {n:3d} ビット")
    print("  → どこまで入れ子にしても「自分を含む完全な記述」は完成しない (無限後退)。")
    print("    フォン・ノイマンの解: 記述は『解釈して構築』(A) と『解釈せず複写』(B) の")
    print("    2通りに使う。φ は φ を含まなくてよい。")

    header("実験4: 付加機 D を持つ A+B+C+D + φ(A+B+C+D) — D も遺伝する")
    show_lineage(Lineage.run(self_reproducing(("A", "B", "C", "D")), 3))

    header("実験5: 突然変異 — φ の1ビットが変わると、その変化が子孫に遺伝する")
    anc = self_reproducing(("A", "B", "C", "D"))
    print(f"祖先の φ = {anc.tape}  (D は 4番目の符号語 = ビット12〜15)")
    lin = Lineage.run(anc, 4, mutate={1: 13})
    print("第1世代の子の φ のビット13を反転 (D=0011 → 0111 = H):")
    show_lineage(lin)
    print("  注目: 第1世代の変異個体は『体は D のまま、テープだけ H』。")
    print("  体に H が現れるのは、変異テープから A が作った次の世代から (遺伝子型→表現型)。")
    print("  以後 [A+B+C+H] + φ(A+B+C+H) は自己複製し、変異が子孫に受け継がれる。")

    header("実験6: 致死変異 — A の符号を壊すと子は不妊")
    lin = Lineage.run(anc, 4, mutate={1: 0})
    print("第1世代の子の φ のビット0を反転 (A=0000 → 1000 = I):")
    show_lineage(lin)
    print("  変異テープ保持者 (体は正常) は毎世代 [I+B+C+D] を1体作るが、")
    print("  [I+B+C+D] は A を持たないので自分では増えない。")

    header("おまけ: 記述 φ はただのビット列")
    bits = encode(("A", "B", "C"))
    print(f"φ(A+B+C) = {bits} → decode → {decode(bits)}")
    print(f"このビット列を解釈すると機械、解釈しなければデータ: {Tape(bits)}")


if __name__ == "__main__":
    main()
