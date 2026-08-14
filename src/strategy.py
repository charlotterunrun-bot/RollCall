"""Student selection strategies."""
import random

import config


def _history_rounds(student, today: str) -> int:
    return sum(1 for d, v in student.records.items() if d != today and v)


def seq_sort_key(s):
    if s.seq_num is not None:
        return (0, s.seq_num, s.row)
    return (1, s.row)


def next_student(students, today: str, strategy: str, appeared: set):
    """Return the next Student to show, or None when all done for today.

    `appeared` is a mutable set of student ids already shown in the current
    round; it is cleared internally when a new round begins.
    """
    candidates = [s for s in students if today not in s.records and s.id not in appeared]
    if not candidates:
        appeared.clear()
        candidates = [s for s in students if today not in s.records]
    if not candidates:
        return None

    # "计重复" -> restrict to students with the fewest historical (non-today) marks.
    if strategy in (config.STRATEGY_RANDOM_COUNT, config.STRATEGY_SEQ_COUNT):
        min_round = min(_history_rounds(s, today) for s in candidates)
        candidates = [s for s in candidates if _history_rounds(s, today) == min_round]

    if strategy in (config.STRATEGY_RANDOM_COUNT, config.STRATEGY_RANDOM_NO_COUNT):
        return random.choice(candidates)
    return min(candidates, key=seq_sort_key)
