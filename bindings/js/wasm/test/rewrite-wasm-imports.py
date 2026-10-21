# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rewrite a module's import section the way JSR does on publish: every
import module name becomes a relative specifier ("env" -> "./env"). Used by
the facade tests to check that a registry-served module still instantiates.
Function imports only, which is all the libmorpheus module declares."""

import sys
src, dst = sys.argv[1], sys.argv[2]
data = open(src, "rb").read()
def leb_read(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
        if not c & 0x80: return r, i
def leb(n):
    out = bytearray()
    while True:
        c = n & 0x7f; n >>= 7
        if n: out.append(c | 0x80)
        else: out.append(c); return bytes(out)
out = bytearray(data[:8]); i = 8
while i < len(data):
    sid = data[i]; size, j = leb_read(data, i + 1); payload = data[j:j+size]; i = j + size
    if sid == 2:
        count, k = leb_read(payload, 0); new = bytearray(leb(count))
        for _ in range(count):
            ml, k = leb_read(payload, k); mod = payload[k:k+ml]; k += ml
            fl, k = leb_read(payload, k); fld = payload[k:k+fl]; k += fl
            kind = payload[k]; k += 1
            assert kind == 0, "function imports only"
            typ, k = leb_read(payload, k)
            mod = b"./" + mod
            new += leb(len(mod)) + mod + leb(len(fld)) + fld + bytes([kind]) + leb(typ)
        assert k == len(payload); payload = bytes(new)
    out += bytes([sid]) + leb(len(payload)) + payload
open(dst, "wb").write(out)
