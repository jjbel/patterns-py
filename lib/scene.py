"""Core geometry model for lithography pattern generation.

Everything is stored in **integer image pixels** (origin top-left, x right, y down).
This is the ground truth: a 1px feature is exactly one pixel, with no floating-point or
anti-alias blur. Microns are a convenience layer on top -- ``Pattern.um`` converts a micron
value to the nearest integer pixel using the fixed projection scale.

The GDS exporter derives micron coordinates from these same integer pixels, so the vector
and raster outputs can never disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# Fixed projection scale: the full 3840 px DMD width spans 1100 um on the wafer.
DEFAULT_FIELD_UM = 1100.0
DEFAULT_WIDTH_PX = 3840
DEFAULT_HEIGHT_PX = 2160


@dataclass
class Box:
    """Axis-aligned rectangle in integer pixels, top-left corner at (x, y)."""

    x: int
    y: int
    w: int
    h: int
    intensity: int = 255

    def translated(self, dx: int, dy: int) -> "Box":
        return replace(self, x=self.x + dx, y=self.y + dy)

    def bbox(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


@dataclass
class Polygon:
    """General polygon with integer-pixel vertices."""

    points: list[tuple[int, int]]
    intensity: int = 255

    def translated(self, dx: int, dy: int) -> "Polygon":
        return Polygon([(px + dx, py + dy) for px, py in self.points], self.intensity)

    def bbox(self) -> tuple[int, int, int, int]:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


@dataclass
class ShapeGroup:
    """A translatable, composable collection of shapes with a local origin.

    Builders return groups so patterns can be assembled by placing groups at pixel
    coordinates (see :meth:`Pattern.place`).
    """

    shapes: list = field(default_factory=list)

    def add(self, shape) -> "ShapeGroup":
        if isinstance(shape, ShapeGroup):
            self.shapes.extend(shape.shapes)
        else:
            self.shapes.append(shape)
        return self

    def translated(self, dx: int, dy: int) -> "ShapeGroup":
        return ShapeGroup([s.translated(dx, dy) for s in self.shapes])

    def bbox(self) -> tuple[int, int, int, int]:
        """Bounding box (x, y, w, h) over all shapes; (0, 0, 0, 0) if empty."""
        if not self.shapes:
            return (0, 0, 0, 0)
        boxes = [s.bbox() for s in self.shapes]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes)
        y1 = max(b[1] + b[3] for b in boxes)
        return (x0, y0, x1 - x0, y1 - y0)


class Pattern:
    """A full pattern: a canvas plus a flat list of shapes in integer pixels."""

    def __init__(
        self,
        name: str,
        field_um: float = DEFAULT_FIELD_UM,
        width_px: int = DEFAULT_WIDTH_PX,
        height_px: int = DEFAULT_HEIGHT_PX,
        layer: tuple[int, int] = (1, 0),
    ):
        self.name = name
        self.width_px = width_px
        self.height_px = height_px
        self.layer = layer
        # microns per pixel: the full width spans field_um microns.
        self.um_per_px = field_um / width_px
        self.shapes: list = []

    @property
    def px_per_um(self) -> float:
        return 1.0 / self.um_per_px

    def um(self, value_um: float) -> int:
        """Convert a micron length to the nearest integer pixel (keeps features crisp)."""
        return round(value_um * self.px_per_um)

    def add(self, shape_or_group) -> "Pattern":
        if isinstance(shape_or_group, ShapeGroup):
            self.shapes.extend(shape_or_group.shapes)
        else:
            self.shapes.append(shape_or_group)
        return self

    def place(self, group: ShapeGroup, x: int, y: int) -> "Pattern":
        """Add ``group`` translated so its local origin lands at pixel (x, y)."""
        return self.add(group.translated(x, y))

    def iter_boxes(self):
        """Yield every shape as a Box, for exporters that only need rectangles."""
        for s in self.shapes:
            if isinstance(s, Box):
                yield s

    def iter_polygons(self):
        for s in self.shapes:
            if isinstance(s, Polygon):
                yield s
