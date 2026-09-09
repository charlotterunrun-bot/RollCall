"""Regression tests for the v1 student-selection rules."""
import config
from excel_io import Student
from strategy import next_student


TODAY = "2026-09-09"


def test_day_is_finished_after_every_student_is_recorded():
    student = Student(2, "1", "S001", "Example", "A", {TODAY: "到"})

    assert next_student([student], TODAY, config.DEFAULT_STRATEGY, set()) is None


def test_counting_strategies_prioritize_fewer_historical_records():
    fewer = Student(2, "1", "S001", "Fewer", "A", {"2026-09-08": "到"})
    more = Student(
        3,
        "2",
        "S002",
        "More",
        "A",
        {"2026-09-07": "到", "2026-09-08": "假"},
    )

    for strategy in (config.STRATEGY_RANDOM_COUNT, config.STRATEGY_SEQ_COUNT):
        assert next_student([more, fewer], TODAY, strategy, set()).id == fewer.id


def test_random_selection_excludes_students_already_recorded_today():
    recorded = Student(2, "1", "S001", "Recorded", "A", {TODAY: "到"})
    pending = Student(3, "2", "S002", "Pending", "A")

    assert next_student(
        [recorded, pending], TODAY, config.STRATEGY_RANDOM_NO_COUNT, set()
    ).id == pending.id


def test_sequence_selection_orders_students_by_legal_sequence_number():
    ten = Student(2, "10", "S010", "Ten", "A")
    two = Student(3, "2", "S002", "Two", "A")
    invalid = Student(4, "unknown", "S000", "Invalid", "A")
    appeared = set()

    selected = []
    for _ in range(3):
        student = next_student(
            [ten, invalid, two], TODAY, config.STRATEGY_SEQ_NO_COUNT, appeared
        )
        selected.append(student.seq)
        appeared.add(student.id)

    assert selected == ["2", "10", "unknown"]
