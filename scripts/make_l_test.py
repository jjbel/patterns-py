"""Single L-shape test structure.

Run:  python scripts/make_l_test.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib._bootstrap import OUT
from lib import Pattern, l_shape, write_png


p = Pattern("l_test")

# Single L made from horizontal lines only.
L = l_shape(line_width=20, n=5, q=500)
p.place(L, 100, 100)

write_png(p, OUT / "l_test_white.png", "white")

print(f"wrote {OUT / 'l_test_white.png'}")
