"""Pure window geometry calculations shared by the first-run and main windows."""

from PySide6.QtCore import QMargins, QPoint, QRect, QSize

DEFAULT_CLIENT_SIZE = QSize(640, 480)
SAFETY_MARGIN = 12


def _safe_available(available: QRect) -> QRect:
    return available.adjusted(
        SAFETY_MARGIN,
        SAFETY_MARGIN,
        -SAFETY_MARGIN,
        -SAFETY_MARGIN,
    )


def fit_window_geometry(
    available: QRect,
    frame_margins: QMargins = QMargins(),
    desired: QSize = DEFAULT_CLIENT_SIZE,
) -> tuple[QSize, QRect]:
    """Return a clamped client size and centered frame inside available space."""
    safe = _safe_available(available)
    max_client = QSize(
        max(1, safe.width() - frame_margins.left() - frame_margins.right()),
        max(1, safe.height() - frame_margins.top() - frame_margins.bottom()),
    )
    client = QSize(
        min(desired.width(), max_client.width()),
        min(desired.height(), max_client.height()),
    )
    frame_size = QSize(
        client.width() + frame_margins.left() + frame_margins.right(),
        client.height() + frame_margins.top() + frame_margins.bottom(),
    )
    frame = QRect(QPoint(0, 0), frame_size)
    frame.moveCenter(safe.center())
    if frame.left() < safe.left():
        frame.moveLeft(safe.left())
    if frame.top() < safe.top():
        frame.moveTop(safe.top())
    if frame.right() > safe.right():
        frame.moveRight(safe.right())
    if frame.bottom() > safe.bottom():
        frame.moveBottom(safe.bottom())
    return client, frame


def frame_fits_available(frame: QRect, available: QRect) -> bool:
    """Return whether a frame remains inside the safe available rectangle."""
    return _safe_available(available).contains(frame)
