from PySide6.QtCore import QMargins, QRect, QSize


def test_fit_window_geometry_keeps_default_on_normal_screen():
    from window_geometry import fit_window_geometry

    client, frame = fit_window_geometry(QRect(0, 0, 1920, 1080), QMargins(8, 32, 8, 8))

    assert client == QSize(640, 480)
    assert frame == QRect(632, 280, 656, 520)


def test_fit_window_geometry_clamps_client_and_frame_on_small_screen():
    from window_geometry import fit_window_geometry

    client, frame = fit_window_geometry(QRect(100, 50, 520, 380), QMargins(10, 30, 10, 10))

    assert client == QSize(476, 316)
    assert frame == QRect(112, 62, 496, 356)


def test_frame_fits_available_reports_existing_frame_without_refit():
    from window_geometry import frame_fits_available

    available = QRect(0, 0, 800, 600)
    assert frame_fits_available(QRect(80, 60, 640, 480), available)
    assert not frame_fits_available(QRect(80, 60, 640, 480), QRect(0, 0, 700, 500))


def test_fit_window_geometry_keeps_tiny_screen_frame_valid_and_on_screen():
    from window_geometry import fit_window_geometry, frame_fits_available

    available = QRect(0, 0, 10, 10)
    client, frame = fit_window_geometry(available, QMargins(8, 32, 8, 8))

    assert client.width() >= 1
    assert client.height() >= 1
    assert frame.isValid()
    assert available.contains(frame)
    assert frame_fits_available(frame, available)
