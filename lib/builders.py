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


def checkerboard(
    square_size: int, nx: int, ny: int, intensity: int = 255
) -> ShapeGroup:
    """An ``nx`` by ``ny`` checkerboard of filled squares (top-left square filled)."""
    s = int(square_size)
    shapes = []
    for j in range(ny):
        for i in range(nx):
            if (i + j) % 2 == 0:
                shapes.append(Box(i * s, j * s, s, s, intensity))
    return ShapeGroup(shapes)


def l_shape(line_width: int, n: int, q: int, intensity: int = 255) -> ShapeGroup:
    """``n`` horizontal lines of length ``q`` with a checkerboard block on the right.

    The checkerboard has side length ``2n - 1`` squares, with filled squares touching
    the horizontal lines exactly. ``n - 1`` additional stepped L-shapes extend rightward
    from the checkerboard edge and sit on the checkerboard gaps.
    """
    lw = int(line_width)
    if lw < 1:
        raise ValueError("line_width must be >= 1 px")
    n = int(n)

    shapes = []
    shapes.extend([Box(0, i * (lw + lw), q, lw, intensity) for i in range(n)])

    board_x = q
    board = checkerboard(lw, 2 * n - 1, 2 * n - 1, intensity)
    shapes.extend(shape.translated(board_x, 0) for shape in board.shapes)

    right_x = board_x + (2 * n - 1) * lw
    for i in range(max(0, n - 1)):
        length = q + i * lw
        y = (2 * i + 1) * lw
        shapes.append(Box(right_x, y, length + i * lw, lw, intensity))
        # vertical line: all tops line up at (2*lw - q); grow the height down to the
        # existing bottom (y + lw) so it still meets its horizontal segment
        shapes.append(
            Box(right_x + length + i * lw, 2 * lw - q, lw, y - lw + q, intensity)
        )

    # normalize so the group's bbox top-left sits at the local origin (0, 0)
    group = ShapeGroup(shapes)
    bx, by, _, _ = group.bbox()
    return group.translated(-bx, -by)


def nested_ls(
    n: int, line_widths, q_factor: float = 12, intensity: int = 255
) -> ShapeGroup:
    """Place one :func:`l_shape` per line width, all sharing a common (top-left) origin.

    Each L already has a top-left origin, so they are simply overlaid at (0, 0); larger
    line widths give larger L's that nest around the smaller ones. Intersections between
    L's are not checked.
    """
    out = ShapeGroup()
    for lw in line_widths:
        q = max(1, round(q_factor * lw))
        out.add(l_shape(lw, n, q, intensity))
    return out
