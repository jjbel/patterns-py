"""GDSII export via the standalone KLayout scripting API (``klayout.db``).

Geometry is derived from the pattern's integer pixels, so the GDS matches the raster
exactly. Per-pixel intensity is intentionally *ignored*: GDSII stores binary polygons on a
layer/datatype and has no notion of grayscale dose.
"""

from __future__ import annotations

import klayout.db as kdb


def write_gds(pattern, path) -> None:
    layout = kdb.Layout()
    layout.dbu = 0.001  # 1 nm database grid
    top = layout.create_cell(pattern.name)
    lyr = layout.layer(*pattern.layer)

    W, H, s = pattern.width_px, pattern.height_px, pattern.um_per_px

    def to_um(px, py):
        # centre the origin on the field and flip y so GDS is y-up
        return ((px - W / 2) * s, (H / 2 - py) * s)

    for b in pattern.iter_boxes():
        x0, y0 = to_um(b.x, b.y)
        x1, y1 = to_um(b.x + b.w, b.y + b.h)
        # intensity (b.intensity) deliberately unused -- GDS is binary
        top.shapes(lyr).insert(kdb.DBox(x0, y1, x1, y0))

    for p in pattern.iter_polygons():
        pts = [kdb.DPoint(*to_um(px, py)) for px, py in p.points]
        top.shapes(lyr).insert(kdb.DPolygon(pts))

    layout.write(str(path))
