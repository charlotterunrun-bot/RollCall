from datetime import date

import pytest


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_write_failure_keeps_current_student_and_data(monkeypatch, qapp):
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    win = MainWindow(data=data, acquire_lock=False)
    win.current = student
    win._finished = False
    calls = []
    monkeypatch.setattr("excel_io.write_record", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("disk")))
    monkeypatch.setattr(win, "_begin_pick", lambda: calls.append("pick"))
    monkeypatch.setattr("main_window.QMessageBox.critical", lambda *a, **k: None)
    win.on_record("到")
    assert win.current is student
    assert data.students[0].records == {}
    assert calls == []
    win.close()


def test_stale_click_after_date_rollover_does_not_write(monkeypatch, qapp):
    import main_window
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    win = MainWindow(data=data, acquire_lock=False)
    win.today = "2026-09-09"
    monkeypatch.setattr(main_window, "current_date_string", lambda: "2026-09-10")
    writes = []
    monkeypatch.setattr(main_window.excel_io, "load_record", lambda *a, **k: data)
    monkeypatch.setattr(main_window.excel_io, "write_record", lambda *a, **k: writes.append(a))
    monkeypatch.setattr("main_window.QMessageBox.information", lambda *a, **k: None)
    win.current = student
    win.on_record("到")
    assert writes == []
    assert student.records == {}
    win.close()


def test_completed_day_disables_record_buttons(qapp):
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {"2026-09-09": "到"})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    win = MainWindow(data=data, acquire_lock=False)
    win.start_rollcall()
    assert win._finished is True
    assert not win.btn_present.isEnabled()
    win.close()


def test_session_lock_covers_initialization_window(qapp, tmp_path):
    from errors import AppError
    from init_window import InitWindow
    from main_window import acquire_session_lock

    target = tmp_path / "record.xlsx"
    lock = acquire_session_lock(target)
    window = InitWindow(target_path=target, session_lock=lock)
    try:
        with pytest.raises(AppError) as exc:
            acquire_session_lock(target)
        assert exc.value.code == "storage_locked"
    finally:
        window.close()
