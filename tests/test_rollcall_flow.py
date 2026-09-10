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
    monkeypatch.setattr("main_window.i18n.critical", lambda *a, **k: None)
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
    monkeypatch.setattr("main_window.i18n.information", lambda *a, **k: None)
    win.current = student
    win.on_record("到")
    assert writes == []
    assert student.records == {}
    win.close()


def test_completed_day_disables_record_buttons(qapp, monkeypatch):
    import main_window
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    monkeypatch.setattr(main_window, "current_date_string", lambda: "2026-09-09")
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


def test_failed_main_window_construction_does_not_steal_init_lock(qapp, tmp_path, monkeypatch):
    import main_window
    from errors import AppError
    from excel_io import RollCallData, Student
    from init_window import InitWindow
    from main_window import MainWindow, acquire_session_lock

    target = tmp_path / "record.xlsx"
    lock = acquire_session_lock(target)
    init = InitWindow(target_path=target, session_lock=lock)
    failure = {"enabled": True}

    def load(*args, **kwargs):
        if failure["enabled"]:
            raise AppError("excel.invalid_file", path=str(target))
        return RollCallData([Student(2, "1", "S1", "A", {}, {})], {}, source_path=target, sheet_name="record")

    monkeypatch.setattr(main_window, "_load_with_sheet_choice", load)
    with pytest.raises(AppError):
        MainWindow(session_lock=init.supplied_session_lock())
    with pytest.raises(AppError) as exc:
        acquire_session_lock(target)
    assert exc.value.code == "storage_locked"

    failure["enabled"] = False
    window = MainWindow(session_lock=init.supplied_session_lock())
    init.take_session_lock()
    window.close()
    init.close()
    released = acquire_session_lock(target)
    released.unlock()


def test_date_refresh_failure_is_latched_until_explicit_reload(qapp, monkeypatch):
    import main_window
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    dates = iter(["2026-09-09", "2026-09-10", "2026-09-10", "2026-09-10"])
    monkeypatch.setattr(main_window, "current_date_string", lambda: next(dates, "2026-09-10"))
    win = MainWindow(data=data, acquire_lock=False)
    warnings = []
    monkeypatch.setattr(main_window, "current_date_string", lambda: "2026-09-10")
    monkeypatch.setattr(main_window, "_load_with_sheet_choice", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("locked")))
    monkeypatch.setattr(main_window.i18n, "warning", lambda *a, **k: warnings.append(a[1]))
    win.today = "2026-09-09"
    assert win._ensure_current_day() is False
    assert win._ensure_current_day() is False
    assert warnings == ["新日期读取失败"]
    monkeypatch.setattr(main_window, "_load_with_sheet_choice", lambda *a, **k: data)
    win.reload_record = lambda **kwargs: (setattr(win, "_pending_date_error", None), data)[1]
    win.reload_record(show_success=False)
    win.close()


def test_checked_successful_save_ends_session_with_one_dialog(monkeypatch, qapp):
    import main_window
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    win = MainWindow(data=data, acquire_lock=False)
    win.current = student
    win._finished = False
    win.end_checkbox.setChecked(True)
    dialogs = []
    picks = []
    closed = []
    monkeypatch.setattr(main_window.excel_io, "write_record", lambda *args, **kwargs: data)
    monkeypatch.setattr(main_window.i18n, "information", lambda *args: dialogs.append(args[1:]))
    monkeypatch.setattr(win, "_begin_pick", lambda **kwargs: picks.append(kwargs))
    monkeypatch.setattr(win, "close", lambda: closed.append(True))

    win.on_record("到")

    assert dialogs == [("本次点名结束", "本次点名已结束。")]
    assert picks == []
    assert closed == [True]
    assert win.data is data
    assert student.records == {}
    win.deleteLater()


def test_checked_save_failure_keeps_session_open_and_checked(monkeypatch, qapp):
    import main_window
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    win = MainWindow(data=data, acquire_lock=False)
    win.current = student
    win._finished = False
    win.end_checkbox.setChecked(True)
    closed = []
    monkeypatch.setattr(main_window.excel_io, "write_record", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("disk")))
    monkeypatch.setattr(main_window.i18n, "critical", lambda *args, **kwargs: None)
    monkeypatch.setattr(win, "close", lambda: closed.append(True))

    win.on_record("到")

    assert win.current is student
    assert win.end_checkbox.isChecked()
    assert closed == []
    win.close()


def test_completed_screen_rolls_over_and_next_day_can_start(qapp, monkeypatch):
    import main_window
    from main_window import MainWindow
    from excel_io import Student, RollCallData

    student = Student(2, "1", "S1", "A", {}, {"2026-09-09": "到"})
    data = RollCallData([student], {}, source_path="record.xlsx", sheet_name="record")
    today = {"value": "2026-09-09"}
    monkeypatch.setattr(main_window, "current_date_string", lambda: today["value"])
    monkeypatch.setattr(main_window, "_load_with_sheet_choice", lambda *a, **k: data)
    monkeypatch.setattr(main_window.i18n, "information", lambda *a, **k: None)
    win = MainWindow(data=data, acquire_lock=False)
    win.start_rollcall()
    assert win._finished is True
    today["value"] = "2026-09-10"
    win._check_date_timer()
    assert win.stack.currentIndex() == 0
    assert win._finished is False
    win.start_rollcall()
    assert win.stack.currentIndex() == 1
    assert win.current is student
    win.close()
