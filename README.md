# patterns-py

Script-driven lithography pattern generation for the HackerFab DMD projector
(TI DLP471t, 4K UHD / 16:9). One integer-pixel geometry description produces **both**:

- a **vector GDSII** file (single layer) for KLayout / archival, and
- crisp **raster PNGs** the DMD projects — colourable **red / white / blue**, with
  per-pixel **0–255 intensity** for grayscale dose.

Raster is the ground truth: a 1px feature is exactly one pixel, with **no anti-alias blur**.
The GDS is derived from the same integer pixels, so vector and raster never disagree.
Intensity is raster-only (GDSII has no per-pixel grayscale).

## Scale

Fixed: the full **3840 px** width spans **1100 µm** (`um_per_px = 1100/3840 ≈ 0.286`).
`Pattern.um(x)` converts microns to the nearest integer pixel. Change it per pattern with
`Pattern(name, field_um=..., width_px=..., height_px=...)`.

## Install

```
pip install -r requirements.txt      # klayout, Pillow, numpy
```

## Usage

```
python scripts/make_box.py             # centred square + corner plus-fiducial
python scripts/make_resolution_test.py # full test pattern, tiled into 4 quadrants
python scripts/live_reload.py          # watch sources, re-run, live preview window
```

Outputs land in `out/` (gitignored): a `.gds` plus `_white.png`, `_red.png`, `_blue.png`.

### As a library

```python
from lib import Pattern, box, line_array, checkerboard, plus_fiducial, write_gds, write_png

p = Pattern("demo")
p.place(box(500, 500), 100, 100)                      # px
p.place(line_array(p.um(2), n_lines=5, pitch_factor=2, orientation="v"), 800, 100)
p.place(checkerboard(p.um(10), nx=10, ny=10), 100, 800)
p.place(plus_fiducial(p.um(10)), 60, 60)

write_gds(p, "out/demo.gds")
for c in ("white", "red", "blue"):
    write_png(p, f"out/demo_{c}.png", c)
```

## Concepts

- **Coordinates:** integer image pixels, origin top-left, x→right, y→down. GDS export
  centres the origin and flips y (y-up).
- **Builders** (`lib/builders.py`) return composable `ShapeGroup`s; place them with
  `Pattern.place(group, x, y)`.
- **`line_array`:** `pitch = pitch_factor × line_width` is the **edge-to-edge gap** between
  lines (not the centre-to-centre period).
- **`write_png(pattern, path, color)`:** `color` (`'white'/'red'/'blue'` or an `(r,g,b)`
  multiplier) multiplies the intensity buffer.
- **`preview(pattern, color, show=True)`:** quick downscaled PIL preview (NEAREST — no
  misleading smoothing).

## Layout

`lib/`
  `scene.py` — `Pattern`, `Box`, `Polygon`, `ShapeGroup`, µm↔px scale
  `builders.py` — `box`, `line_array`, `checkerboard`, `plus_fiducial`
  `layout.py` — `flow_layout` (shelf packer), `tile_quadrants`
  `gds.py` — `write_gds`
  `raster.py` — `render_intensity`, `render_rgb`, `write_png`
  `preview.py` — `preview`
  `_bootstrap.py` — `ROOT` / `OUT` paths for scripts
`scripts/` — `make_box.py`, `make_resolution_test.py` (test block built inline here), `live_reload.py`
