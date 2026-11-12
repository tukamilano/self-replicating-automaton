"""Golly の RLE 形式 (多状態) の読み書き.

多状態 RLE の記号:  '.' = 0,  'A'..'X' = 1..24,  'pA'..'pX' = 25..48, …
数字はその後の記号の繰り返し回数、'$' は改行、'!' は終端。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Pattern:
    cells: np.ndarray            # [行, 列] uint8
    rule: str = ""
    comments: list[str] = field(default_factory=list)


def _symbol_value(sym: str) -> int:
    if sym in ".b":
        return 0
    if sym == "o":
        return 1
    if len(sym) == 1:
        return ord(sym) - ord("A") + 1
    return (ord(sym[0]) - ord("p") + 1) * 24 + ord(sym[1]) - ord("A") + 1


_TOKEN = re.compile(r"(\d*)([.boA-X$!]|[p-y][A-X])")


def parse_rle(text: str) -> Pattern:
    comments, body, header = [], [], None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments.append(line)
        elif header is None and line.startswith("x"):
            header = line
        else:
            body.append(line)
    if header is None:
        raise ValueError("RLE ヘッダ (x = ..) が無い")
    h = dict(kv.split("=") for kv in header.replace(" ", "").split(","))
    width, height = int(h["x"]), int(h["y"])
    cells = np.zeros((height, width), dtype=np.uint8)
    r = c = 0
    for count, sym in _TOKEN.findall("".join(body)):
        n = int(count) if count else 1
        if sym == "!":
            break
        if sym == "$":
            r, c = r + n, 0
            continue
        v = _symbol_value(sym)
        if v:
            cells[r, c:c + n] = v
        c += n
    return Pattern(cells, h.get("rule", ""), comments)


def load_rle(path) -> Pattern:
    with open(path, encoding="utf-8") as f:
        return parse_rle(f.read())


def _symbol(v: int) -> str:
    if v == 0:
        return "."
    if v <= 24:
        return chr(ord("A") + v - 1)
    hi, lo = divmod(v - 1, 24)
    return chr(ord("p") + hi - 1) + chr(ord("A") + lo)


def to_rle(cells: np.ndarray, rule: str = "JvN29") -> str:
    height, width = cells.shape
    out: list[str] = [f"x = {width}, y = {height}, rule = {rule}\n"]
    rows = []
    for row in cells:
        nz = np.nonzero(row)[0]
        row = row[: nz[-1] + 1] if len(nz) else row[:0]
        toks, i = [], 0
        while i < len(row):
            j = i
            while j < len(row) and row[j] == row[i]:
                j += 1
            n = j - i
            toks.append((str(n) if n > 1 else "") + _symbol(int(row[i])))
            i = j
        rows.append("".join(toks))
    body = "$".join(rows) + "!"
    out += [body[i:i + 70] + "\n" for i in range(0, len(body), 70)]
    return "".join(out)
