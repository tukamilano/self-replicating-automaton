"""段階1: フォン・ノイマン自己複製の「抽象論理」.

フォン・ノイマンの議論（1948-49 の講演, 『自己増殖オートマトンの理論』）を
そのままコードにしたもの。登場人物は次の4つ:

  A  万能構成機 (universal constructor)  : 記述 φ(X) を読んで機械 X を作る
  B  複製機     (copier)                  : 記述 φ(X) をそのまま複写する
  C  制御機     (controller)              : A → B → 「子に複写テープを渡す」の順に起動する
  φ  記述テープ (description)             : 機械の設計図。ビット列

ポイントは「A+B+C に φ(A+B+C) を持たせる」こと。テープは機械の"部品"としては
記述されない（φ は φ 自身を含まない）。テープは B で"複写"されるだけなので、
自己言及の無限後退が起きない。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 記述言語: 部品1個 = 4ビットの符号語
# ---------------------------------------------------------------------------
PART_BITS = 4
# 符号 i (0..15) が表す部品名。A, B, C だけが機能を持ち、他は「付加機 D 等」(機能なし)
PART_NAMES = "ABCDEFGHIJKLMNOP"
FUNCTIONAL = {"A", "B", "C"}


def encode(parts: tuple[str, ...]) -> str:
    """部品列 → 記述 φ (ビット列)。"""
    return "".join(format(PART_NAMES.index(p), f"0{PART_BITS}b") for p in parts)


def decode(bits: str) -> tuple[str, ...]:
    """記述 φ → 部品列。A が内部で使うのと同じ読み方。"""
    if len(bits) % PART_BITS:
        raise ValueError("テープ長が符号語長の倍数でない")
    return tuple(PART_NAMES[int(bits[i:i + PART_BITS], 2)]
                 for i in range(0, len(bits), PART_BITS))


@dataclass(frozen=True)
class Tape:
    bits: str

    def mutate(self, i: int) -> "Tape":
        """i ビット目を反転した（突然変異した）テープ。"""
        flipped = "1" if self.bits[i] == "0" else "0"
        return Tape(self.bits[:i] + flipped + self.bits[i + 1:])

    def __str__(self) -> str:
        return " ".join(self.bits[i:i + PART_BITS]
                        for i in range(0, len(self.bits), PART_BITS))


# ---------------------------------------------------------------------------
# 部品の働き
# ---------------------------------------------------------------------------
def constructor_A(tape: Tape, log: list[str]) -> tuple[str, ...]:
    """A: テープを先頭から1符号語ずつ読み、対応する部品を組み立てる。"""
    built: list[str] = []
    for i in range(0, len(tape.bits), PART_BITS):
        word = tape.bits[i:i + PART_BITS]
        part = PART_NAMES[int(word, 2)]
        built.append(part)
        log.append(f"A: 符号 {word} を読み → 部品 {part} を構築")
    return tuple(built)


def copier_B(tape: Tape, log: list[str]) -> Tape:
    """B: テープの中身を解釈せず、1ビットずつ写す。"""
    copy = "".join(bit for bit in tape.bits)
    log.append(f"B: テープ {len(copy)} ビットを複写")
    return Tape(copy)


@dataclass(frozen=True)
class Machine:
    parts: tuple[str, ...]
    tape: Tape | None = None
    name: str = field(default="", compare=False)

    def has(self, part: str) -> bool:
        return part in self.parts

    def reproduce(self, log: list[str] | None = None) -> "Machine | None":
        """C(制御機) の手順に従って子を作る。作れなければ None。"""
        log = [] if log is None else log
        if not self.has("C"):
            log.append("C が無い: 何も起動されない")
            return None
        if self.tape is None:
            log.append("C: テープが無い: 設計図が無いので何も作れない")
            return None
        if not self.has("A"):
            log.append("C: A が無い: 設計図を読めても組み立てられない")
            return None
        log.append("C: A を起動")
        child_parts = constructor_A(self.tape, log)
        if self.has("B"):
            log.append("C: B を起動")
            child_tape: Tape | None = copier_B(self.tape, log)
        else:
            log.append("C: B が無い: 子はテープを受け取れない")
            child_tape = None
        log.append("C: 複写テープを子に取り付けて切り離す")
        return Machine(child_parts, child_tape)

    def __str__(self) -> str:
        body = "+".join(self.parts) or "(空)"
        if self.tape is None:
            return f"[{body}] テープなし"
        return f"[{body}] + φ({'+'.join(decode(self.tape.bits))})"


def self_reproducing(parts: tuple[str, ...]) -> Machine:
    """X に φ(X) を持たせた機械 X + φ(X) を作る。"""
    return Machine(parts, Tape(encode(parts)))


# ---------------------------------------------------------------------------
# 系譜シミュレーション
# ---------------------------------------------------------------------------
@dataclass
class Lineage:
    """各世代で全個体が1回ずつ子を作る（親は残る）。"""
    generations: list[list[Machine]]

    @classmethod
    def run(cls, ancestor: Machine, n_gen: int,
            mutate: dict[int, int] | None = None) -> "Lineage":
        """mutate={世代: ビット位置} で、その世代の最初の子のテープを変異させる。"""
        mutate = mutate or {}
        gens = [[ancestor]]
        for g in range(1, n_gen + 1):
            parents = gens[-1]
            children = [c for c in (m.reproduce() for m in parents) if c is not None]
            if g in mutate and children and children[0].tape is not None:
                first = children[0]
                children[0] = Machine(first.parts, first.tape.mutate(mutate[g]))
            gens.append(parents + children)
        return cls(gens)


def naive_self_description_lengths(n_parts: int, depth: int) -> list[int]:
    """B を使わず「テープも含めて機械全体を記述しよう」とした場合の記述長.

    機械 M = 部品 + テープ T。T = φ(M) には部品とテープ T 自身の記述が要る:
        |φ_k| = 部品の記述長 + |φ_{k-1}| (+ 区切り)
    深さ k を増やしても長さが単調増加し、固定点 (|T| = |φ(M)|) に達しない。
    """
    lengths = [n_parts * PART_BITS]
    for _ in range(depth - 1):
        lengths.append(n_parts * PART_BITS + PART_BITS + lengths[-1])
    return lengths
