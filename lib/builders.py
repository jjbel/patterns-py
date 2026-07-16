"""Single-call pattern builders. Each returns a :class:`ShapeGroup` with local origin
(0, 0), so results can be composed and placed anywhere with ``Pattern.place``.

All dimensions are in integer pixels unless they come from ``Pattern.um(...)``.
"""

from __future__ import annotations

from .scene import Box, ShapeGroup


def box(w: int, h: int, intensity: int = 255) -> ShapeGroup:
    """A single filled rectangle with top-left at the local origin."""
    return ShapeGroup([Box(0, 0, w, h, intensity)])


def plus_fiducial(square_size: int, intensity: int = 255) -> ShapeGroup:
    """A plus/cross of 5 identical squares: one centre + 4 orthogonal neighbours.

    Overall bounding box is ``3 * square_size`` on each side.
    """
    s = square_size
    # grid positions (col, row) in units of s: centre plus up/down/left/right
    cells = [(1, 1), (1, 0), (1, 2), (0, 1), (2, 1)]
    return ShapeGroup([Box(c * s, r * s, s, s, intensity) for c, r in cells])


def line_array(
    line_width: int,
    n_lines: int = 4,
    pitch_factor: float = 2,
    orientation: str = "v",
    length: int | None = None,
    intensity: int = 255,
) -> ShapeGroup:
    """An array of ``n_lines`` parallel lines.

    ``pitch`` is the edge-to-edge gap between adjacent lines and equals
    ``pitch_factor * line_width`` (so the centre-to-centre period is
    ``line_width * (1 + pitch_factor)``).

    ``orientation``: ``'v'`` = vertical lines packed left->right; ``'h'`` = horizontal
    lines stacked top->down. ``length`` is the long dimension of each line (defaults to a
    compact value).
    """
    lw = int(line_width)
    if lw < 1:
        raise ValueError("line_width must be >= 1 px")
    gap = round(pitch_factor * lw)  # edge-to-edge spacing, integer px
    step = lw + gap  # centre-to-centre period
    cross = n_lines * lw + (n_lines - 1) * gap  # extent across the array
    if length is None:
        length = max(6 * lw, cross)

    shapes = []
    for i in range(n_lines):
        off = i * step
        if orientation == "v":
            shapes.append(Box(off, 0, lw, length, intensity))
        elif orientation == "h":
            shapes.append(Box(0, off, length, lw, intensity))
        else:
            raise ValueError("orientation must be 'v' or 'h'")
    return ShapeGroup(shapes)


def checkerboard(square_size: int, nx: int, ny: int, intensity: int = 255) -> ShapeGroup:
    """An ``nx`` by ``ny`` checkerboard of filled squares (top-left square filled)."""
    s = int(square_size)
    shapes = []
    for j in range(ny):
        for i in range(nx):
            if (i + j) % 2 == 0:
                shapes.append(Box(i * s, j * s, s, s, intensity))
    return ShapeGroup(shapes)


def l_shape(line_width: int, n: int, q: int, intensity: int = 255) -> ShapeGroup:
    """An L-shaped test structure: a horizontal line array and a vertical line array
    meeting at a checkerboard elbow.

    Shaped like the letter "L": the vertical arm runs up the left, the horizontal arm runs
    along the bottom, and they meet at a checkerboard elbow in the bottom-left. Following the
    horizontal arm from the elbow (left) outward to its far end (right):
      * ``n - 1`` horizontal lines of length ``q`` that touch ``n - 1`` vertical lines of
        length ``q`` -- the corner, where the arm turns upward
      * a checkerboard of side ``n`` (``n x n`` cells of ``line_width``) at the elbow
      * ``n`` horizontal lines of length ``q``  (the far horizontal arm)

    Lines are ``line_width`` wide at pitch ``2 * line_width`` (equal line/space). The
    returned group has a top-left local origin; its **top-right** bbox corner is an empty
    notch -- the natural anchor for concentric nesting (see :func:`nested_ls`).
    """
    if n < 2:
        raise ValueError("n must be >= 2")
    lw = int(line_width)
    q = int(q)
    pitch = 2 * lw

    def hlines(left, top, k):
        return [Box(left, top + i * pitch, q, lw, intensity) for i in range(k)]

    def vlines(left, top, k):
        return [Box(left + j * pitch, top, lw, q, intensity) for j in range(k)]

    shapes = []
    yh = q  # the horizontal arm sits below the vertical arm (which rises to y = 0)

    # corner (elbow) horizontal lines: n-1 lines, x in [0, q]
    shapes += hlines(0, yh, n - 1)

    # corner vertical lines: n-1 lines rising up (y in [0, q]) at the left, so their bottoms
    # touch the corner horizontal lines
    shapes += vlines(0, 0, n - 1)

    # checkerboard elbow: n x n cells of lw, just right of the corner lines
    shapes += checkerboard(lw, n, n, intensity).translated(q, yh).shapes

    # far horizontal arm: n lines, x in [q + n*lw, 2q + n*lw]
    shapes += hlines(q + n * lw, yh, n)

    return ShapeGroup(shapes)


def nested_ls(n: int, line_widths, q_factor: float = 12, intensity: int = 255) -> ShapeGroup:
    """Place one :func:`l_shape` per line width (all sharing the same ``n``) concentrically,
    aligned on a common bbox **top-right** corner.

    ``q`` scales proportionally with line width (``q = q_factor * line_width``); since every
    other dimension of an L is also a multiple of its line width, the L's are geometrically
    similar and nest cleanly. Overlap between L's is assumed absent (not checked).
    """
    out = ShapeGroup()
    for lw in line_widths:
        q = max(1, round(q_factor * lw))
        L = l_shape(lw, n, q, intensity)
        bx, by, bw, _ = L.bbox()
        # translate so every L's bbox top-right corner lands on a common point (0, 0)
        out.add(L.translated(-(bx + bw), -by))
    # normalise to a top-left origin so the whole group places on-canvas
    gx, gy, _, _ = out.bbox()
    return out.translated(-gx, -gy)
