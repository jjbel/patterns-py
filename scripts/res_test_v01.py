"""Resolution test v01: nested L's, a digit strip (0-9), and pitch=4x line arrays,
with plus fiducials in the 4 corners. Single field -- no quadrant tiling.

Each logical group is one block for flow_layout: all the L's are one block, the digits
are one block, the line arrays are one block.

Run:  python scripts/res_test_v01.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib._bootstrap import OUT
from lib import (
    Pattern,
    nested_ls,
    text,
    line_array,
    plus_fiducial,
    flow_layout,
    write_gds,
    write_png,
)

# --- knobs -----------------------------------------------------------------------
MAX_W = 3600  # wrap width for the top-level block flow
GAP = 120  # spacing between blocks / packed arrays
MARGIN = 40  # fiducial inset from each canvas corner
FIDUCIAL_SQ = 60  # plus-fiducial square size (bbox is 3x this)
L_LINE_WIDTHS = [4, 17, 35]  # nested-L line widths (px)
ARRAY_WIDTHS = (17, 23, 29, 35)  # line-array widths (px); pitch = 4 x line_width
OUT_STEM = "res_test_v01"  # output file stem (also what live_reload.py watches)

p = Pattern("res_test_v01")

# block 1: nested L's (one per line width) -- kept as a single block
l_block = nested_ls(n=5, line_widths=L_LINE_WIDTHS)

# block 2: line arrays, pitch = 4 x line_width, both orientations, at each width
line_groups = [
    line_array(w, n_lines=4, pitch_factor=4, orientation=o)
    for w in ARRAY_WIDTHS
    for o in ("h", "v")
]
line_block = flow_layout(line_groups, max_width=1200, gap=GAP)

# pack the three blocks (each kept whole, order preserved)
block = flow_layout(
    [l_block, line_block], max_width=MAX_W, gap=GAP, sort_by_height=False
)

# centre the combined block on the field
_, _, bw, bh = block.bbox()
p.place(block, (p.width_px - bw) // 2, (p.height_px - bh) // 2)

# plus fiducials in the 4 corners
fid = plus_fiducial(FIDUCIAL_SQ)
fw, fh = fid.bbox()[2], fid.bbox()[3]
for fx in (MARGIN, p.width_px - MARGIN - fw):
    for fy in (MARGIN, p.height_px - MARGIN - fh):
        p.place(fid, fx, fy)

print(f"combined block bbox: {bw} x {bh} px")

# write_gds(p, OUT / f"{OUT_STEM}.gds")
# for c in ("white", "red", "blue"):
for c in "white":
    write_png(p, OUT / f"{OUT_STEM}_{c}.png", c)
