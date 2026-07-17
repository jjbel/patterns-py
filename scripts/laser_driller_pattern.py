"""Laser-driller pattern: line arrays + circle grids, tiled 3x3.

Scale is fixed at 10 px : 1 um (PX_PER_UM) and the canvas is sized to the content, not
to the DMD field -- every knob below is in MICRONS and px() converts. The canvas is
derived from the assembled block's bbox, so the mask is exactly as big as it needs to
be; field_um is back-computed to hold the scale at whatever width results.

Content of one tile:
  - line arrays: 25/50/100 um widths x pitch 2x/4x x both orientations, 500 um long
  - circle grids: 25/50/75 um diameters at pitch 4x
  - plus fiducials in the 4 corners
That tile is replicated into a 3x3 grid.

OUTPUT: GDS is the real deliverable. At 10 px/um the mask is ~13.4 x 10.1 mm, i.e. a
13.6 gigapixel raster -- render_rgb alone would need >200 GB of RAM, so a full-scale
PNG is not writable. GDS is vector and doesn't care. The PNG is therefore re-built at
PREVIEW_PX_PER_UM purely to eyeball the layout; it is NOT the mask.

Layout is manual (hstack/vstack, centred rows) rather than flow_layout, whose shelf
packing top-aligns and reorders.

Run:  python scripts/laser_driller_pattern.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lib._bootstrap import OUT
from lib import (
    Pattern,
    ShapeGroup,
    line_array,
    circle_grid,
    plus_fiducial,
    write_gds,
    write_png,
)

# --- knobs (all lengths in MICRONS) ----------------------------------------------
PX_PER_UM = 10  # projection scale for the mask: 10 px : 1 um
PREVIEW_PX_PER_UM = 0.4  # scale for the eyeball PNG only (see OUTPUT above)

ARRAY_WIDTHS_UM = (25, 50)  # line-array line widths
PITCH_FACTORS = (2, 4)  # line gap = pitch_factor x line_width (edge-to-edge)
N_LINES = 5  # lines per array
LINE_LEN_UM = 500  # long dimension of every line

CIRCLE_DIAMS_UM = (25, 50, 75)  # circle-grid diameters
CIRCLE_PITCH_FACTOR = 2  # circle gap = 4 x diameter (edge-to-edge)
CIRCLE_N = 8  # circles per side of each grid

GAP_UM = 500  # spacing between adjacent groups / rows
MARGIN_UM = 50  # fiducial inset from each tile corner
FIDUCIAL_SQ_UM = 20  # plus-fiducial square (its bbox is 3x this)
TILE_GAP_UM = 200  # spacing between tiles
TILES = 3  # tile the pattern TILES x TILES


# --- manual layout ----------------------------------------------------------------
def _stack(groups, gap: int, axis: int) -> ShapeGroup:
    """Lay groups out along ``axis`` (0 = x, 1 = y), centred on the other axis."""
    dims = [g.bbox() for g in groups]
    # bbox is (x, y, w, h), so the cross-axis size is index 3 for x, index 2 for y
    cross = max(d[3 - axis] for d in dims)
    out = ShapeGroup()
    pos = 0
    for g, (gx, gy, gw, gh) in zip(groups, dims):
        size, gcross = (gw, gh) if axis == 0 else (gh, gw)
        off = (cross - gcross) // 2
        dx, dy = (pos, off) if axis == 0 else (off, pos)
        out.add(g.translated(dx - gx, dy - gy))
        pos += size + gap
    return out


def hstack(groups, gap: int) -> ShapeGroup:
    """Left-to-right, vertically centred."""
    return _stack(groups, gap, axis=0)


def vstack(groups, gap: int) -> ShapeGroup:
    """Top-to-bottom, horizontally centred."""
    return _stack(groups, gap, axis=1)


# --- assembly ---------------------------------------------------------------------
def build(scale: float) -> Pattern:
    """Assemble the whole 3x3 mask at ``scale`` px per um.

    Geometry is defined in microns, so the same call yields the full-scale mask or a
    small preview depending on ``scale``.
    """

    def px(value_um: float) -> int:
        return round(value_um * scale)

    gap = px(GAP_UM)

    # one row per pitch factor: ascending width, h then v within each width
    line_rows = [
        hstack(
            [
                line_array(
                    px(w),
                    n_lines=N_LINES,
                    pitch_factor=pf,
                    orientation=o,
                    length=px(LINE_LEN_UM),
                )
                for w in ARRAY_WIDTHS_UM
                for o in ("h", "v")
            ],
            gap,
        )
        for pf in PITCH_FACTORS
    ]

    # one row of circle grids, ascending diameter
    circle_row = hstack(
        [
            circle_grid(px(d), n=CIRCLE_N, pitch_factor=CIRCLE_PITCH_FACTOR)
            for d in CIRCLE_DIAMS_UM
        ],
        gap,
    )

    content = vstack(line_rows + [circle_row], gap)

    # frame the content, then drop a plus fiducial in each tile corner
    fid_sq = px(FIDUCIAL_SQ_UM)
    fid_span = 3 * fid_sq  # plus_fiducial's bbox is 3x its square
    inset = px(MARGIN_UM)
    pad = inset + fid_span + gap  # keeps the fiducials clear of the content

    cx, cy, cw, ch = content.bbox()
    tile_w = cw + 2 * pad
    tile_h = ch + 2 * pad

    tile = ShapeGroup()
    tile.add(content.translated(pad - cx, pad - cy))
    fid = plus_fiducial(fid_sq)
    for fx in (inset, tile_w - inset - fid_span):
        for fy in (inset, tile_h - inset - fid_span):
            tile.add(fid.translated(fx, fy))

    # canvas is derived from the content: exactly the TILES x TILES grid
    tile_gap = px(TILE_GAP_UM)
    w = TILES * tile_w + (TILES - 1) * tile_gap
    h = TILES * tile_h + (TILES - 1) * tile_gap

    # field_um back-computed so um_per_px == 1 / scale holds at this width
    p = Pattern("laser_driller_pattern", field_um=w / scale, width_px=w, height_px=h)
    if abs(p.px_per_um - scale) > 1e-9:
        raise ValueError(f"scale drifted: {p.px_per_um} != {scale} px/um")

    for i in range(TILES):
        for j in range(TILES):
            p.place(tile, i * (tile_w + tile_gap), j * (tile_h + tile_gap))

    return p


mask = build(PX_PER_UM)
geom = ShapeGroup(mask.shapes)  # wrap so the new diagonal()/area() helpers are usable
diag_um = geom.diagonal() / PX_PER_UM
area_um2 = geom.area() / PX_PER_UM**2  # px -> um^2 (divide by px/um squared)
fill = geom.area() / (mask.width_px * mask.height_px)  # exposed fraction of the canvas
print(
    f"mask:    {mask.width_px} x {mask.height_px} px  "
    f"({mask.width_px / PX_PER_UM:g} x {mask.height_px / PX_PER_UM:g} um)  "
    f"= {mask.width_px * mask.height_px / 1e9:.2f} Gpx"
)
print(f"shapes:  {len(mask.shapes)}")
print(f"diag:    {diag_um:.0f} um  ({diag_um / 1000:.2f} mm)")
print(f"feature: {area_um2 / 1e6:.3f} mm^2 exposed  ({fill:.2%} fill)")
write_gds(mask, OUT / "laser_driller_pattern.gds")

# preview only -- a full-scale PNG is not writable (see OUTPUT in the module docstring)
pv = build(PREVIEW_PX_PER_UM)
print(f"preview: {pv.width_px} x {pv.height_px} px @ {PREVIEW_PX_PER_UM} px/um")
write_png(pv, OUT / "laser_driller_pattern_preview.png", "white")
