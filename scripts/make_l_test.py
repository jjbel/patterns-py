"""Concentric L-shape test structures, one per line width, sharing a top-right corner.

Run:  python scripts/make_l_test.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib._bootstrap import OUT
from lib import Pattern, nested_ls, write_gds, write_png

# --- knobs -----------------------------------------------------------------------
N = 6                                   # squares per checkerboard side / grating count
LINE_WIDTHS_UM = [0.5, 1, 2, 5, 10]     # one L per line width
Q_FACTOR = 12                           # q = Q_FACTOR * line_width (keeps L's self-similar)

p = Pattern("l_test")

line_widths_px = [max(1, p.um(u)) for u in LINE_WIDTHS_UM]
group = nested_ls(N, line_widths_px, q_factor=Q_FACTOR)

# place the nested L's with their top-right corner near the canvas centre-right
_, _, gw, gh = group.bbox()
p.place(group, (p.width_px - gw) // 2, (p.height_px - gh) // 2)

print(f"nested L's bbox: {gw} x {gh} px  (line widths px: {line_widths_px})")

write_gds(p, OUT / "l_test.gds")
for c in ("white", "red", "blue"):
    write_png(p, OUT / f"l_test_{c}.png", c)

print(f"wrote {OUT / 'l_test.gds'} and l_test_[white|red|blue].png")
