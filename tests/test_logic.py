from vn.logic.machine import (Lineage, Machine, Tape, decode, encode,
                              naive_self_description_lengths, self_reproducing)


def test_encode_roundtrip():
    parts = ("A", "B", "C", "D")
    assert decode(encode(parts)) == parts


def test_abc_reproduces_identically():
    m = self_reproducing(("A", "B", "C"))
    child = m.reproduce()
    assert child == m
    assert child.reproduce() == m


def test_population_doubles():
    lin = Lineage.run(self_reproducing(("A", "B", "C")), 5)
    assert [len(g) for g in lin.generations] == [1, 2, 4, 8, 16, 32]
    assert all(x == lin.generations[0][0] for x in lin.generations[-1])


def test_without_B_child_is_sterile():
    m = self_reproducing(("A", "C"))
    child = m.reproduce()
    assert child.parts == ("A", "C") and child.tape is None
    assert child.reproduce() is None


def test_without_tape_or_A_nothing_built():
    assert Machine(("A", "B", "C")).reproduce() is None
    assert self_reproducing(("B", "C")).reproduce() is None


def test_payload_D_inherited():
    lin = Lineage.run(self_reproducing(("A", "B", "C", "D")), 3)
    assert all(m.parts == ("A", "B", "C", "D") for m in lin.generations[-1])


def test_mutation_is_heritable():
    anc = self_reproducing(("A", "B", "C", "D"))
    lin = Lineage.run(anc, 4, mutate={1: 13})
    last = lin.generations[-1]
    carriers = [m for m in last if decode(m.tape.bits)[-1] == "H"]
    # 変異テープの持ち主は第1世代に1体 → 以後倍々: 第4世代で 2^3 = 8 体
    assert len(carriers) == 8
    # 体に変異が現れるのは「変異テープから作られた」子から (遺伝子型→表現型)
    expressed = [m for m in carriers if m.parts[-1] == "H"]
    assert len(expressed) == 7
    assert all(m.tape.bits == encode(m.parts) for m in expressed)


def test_lethal_mutation():
    anc = self_reproducing(("A", "B", "C", "D"))
    lin = Lineage.run(anc, 3, mutate={1: 0})
    sterile = [m for m in lin.generations[-1] if "A" not in m.parts]
    # 変異テープ保持者(体は正常)が毎世代1体ずつ不妊の子を作るだけで、不妊体は増殖しない
    assert len(sterile) == 2
    assert all(m.reproduce() is None for m in sterile)


def test_naive_description_never_fixed_point():
    ls = naive_self_description_lengths(2, 10)
    assert all(b > a for a, b in zip(ls, ls[1:]))


def test_tape_mutate():
    assert Tape("0000").mutate(2).bits == "0010"
