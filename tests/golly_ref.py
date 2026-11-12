"""テスト用オラクル: Golly (gollybase/jvnalgo.cpp) の JvN29 遷移関数の直訳.

可読性ではなく原典との一致を優先している。vn/ca/rules.py をこれと照合する。
Golly は GPL-2 (https://golly.sourceforge.io)。
"""
NORTH, SOUTH, EAST, WEST = 1, 3, 0, 2
FLIPDIR, DIRMASK = 2, 3
CONF, OTRANS, STRANS, TEXC, CDEXC, CEXC = 0x10, 0x20, 0x40, 0x80, 0x80, 1
BIT_ONEXC, BIT_OEXC_EW, BIT_OEXC_NS = 1, 2, 4
BIT_OEXC = BIT_OEXC_NS | BIT_OEXC_EW
BIT_SEXC, BIT_CEXC = 8, 16
BIT_NS_IN, BIT_EW_IN, BIT_NS_OUT, BIT_EW_OUT = 32, 64, 128, 256
BIT_OEXC_OTHER, BIT_SEXC_OTHER = 512, 1024

UNCOMPRESS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 32, 33, 34, 35, 160, 161, 162, 163,
              64, 65, 66, 67, 192, 193, 194, 195, 16, 144, 17, 145]
COMPRESS = {v: i for i, v in enumerate(UNCOMPRESS)}
CRES = [0x22, 0x23, 0x40, 0x41, 0x42, 0x43, 0x10, 0x20, 0x21]


def _bits(mcode, code, d):
    if (code & (TEXC | OTRANS | STRANS | CONF | CEXC)) == 0:
        return 0
    if code & CONF:
        if (mcode & (OTRANS | STRANS)) and ((mcode & DIRMASK) ^ FLIPDIR) == d:
            return 0
        if code & 1:
            return BIT_CEXC
        return 0
    if (code & (OTRANS | STRANS)) == 0:
        return 0
    r = 0
    if (code & DIRMASK) == d:
        if code & OTRANS:
            if d & 1:
                r |= BIT_NS_IN
                r |= BIT_OEXC_NS if code & TEXC else BIT_ONEXC
            else:
                r |= BIT_EW_IN
                r |= BIT_OEXC_EW if code & TEXC else BIT_ONEXC
        elif (code & (STRANS | TEXC)) == (STRANS | TEXC):
            r |= BIT_SEXC
        if (mcode & (OTRANS | STRANS)) and (d ^ (mcode & DIRMASK)) == 2:
            pass
        else:
            if r & BIT_OEXC:
                r |= BIT_OEXC_OTHER
            if r & BIT_SEXC:
                r |= BIT_SEXC_OTHER
    else:
        r |= BIT_NS_OUT if d & 1 else BIT_EW_OUT
    return r


def golly_step(c, n, e, s, w):
    c = UNCOMPRESS[c]
    mbits = (_bits(c, UNCOMPRESS[n], SOUTH) | _bits(c, UNCOMPRESS[w], EAST)
             | _bits(c, UNCOMPRESS[e], WEST) | _bits(c, UNCOMPRESS[s], NORTH))
    if c < CONF:
        c = 2 * c + 1 if mbits & (BIT_OEXC | BIT_SEXC) else 2 * c
        if c > 8:
            c = CRES[c - 9]
    elif c & CONF:
        if mbits & BIT_SEXC:
            c = 0
        else:
            if (mbits & BIT_OEXC) and not (mbits & BIT_ONEXC):
                c = ((c & CDEXC) >> 7) + (CDEXC | CONF)
            else:
                c = ((c & CDEXC) >> 7) + CONF
    else:
        if ((c & OTRANS) and (mbits & BIT_SEXC)) or ((c & STRANS) and (mbits & BIT_OEXC)):
            c = 0
        elif mbits & (BIT_SEXC_OTHER | BIT_OEXC_OTHER | BIT_CEXC):
            c |= 128
        else:
            c &= 127
    return COMPRESS[c]
