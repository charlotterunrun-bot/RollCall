"""Roll-call config persistence (strategy + marquee toggle)."""
import json
import os

import paths

STRATEGY_RANDOM_COUNT = "random_count"
STRATEGY_RANDOM_NO_COUNT = "random_no_count"
STRATEGY_SEQ_COUNT = "seq_count"
STRATEGY_SEQ_NO_COUNT = "seq_no_count"

DEFAULT_STRATEGY = STRATEGY_RANDOM_COUNT
DEFAULT_MARQUEE = True
DEFAULT_MARQUEE_DURATION = 500
MARQUEE_DURATION_MIN = 100
MARQUEE_DURATION_MAX = 10000

STRATEGY_LABELS = {
    STRATEGY_RANDOM_COUNT: "每次随机计重复",
    STRATEGY_RANDOM_NO_COUNT: "每次随机不计重复",
    STRATEGY_SEQ_NO_COUNT: "按序号顺序不计重复",
    STRATEGY_SEQ_COUNT: "按序号顺序计重复",
}

STRATEGY_ORDER = [
    STRATEGY_RANDOM_COUNT,
    STRATEGY_RANDOM_NO_COUNT,
    STRATEGY_SEQ_NO_COUNT,
    STRATEGY_SEQ_COUNT,
]


def _load() -> dict:
    try:
        with open(paths.config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(paths.record_dir(), exist_ok=True)
    with open(paths.config_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_strategy() -> str:
    s = _load().get("strategy")
    return s if s in STRATEGY_LABELS else DEFAULT_STRATEGY


def load_marquee() -> bool:
    return bool(_load().get("marquee", DEFAULT_MARQUEE))


def load_marquee_duration() -> int:
    v = _load().get("marquee_duration", DEFAULT_MARQUEE_DURATION)
    try:
        v = int(v)
    except (TypeError, ValueError):
        return DEFAULT_MARQUEE_DURATION
    return max(MARQUEE_DURATION_MIN, min(MARQUEE_DURATION_MAX, v))


def save_settings(strategy=None, marquee=None, marquee_duration=None) -> None:
    data = _load()
    if strategy is not None:
        data["strategy"] = strategy
    if marquee is not None:
        data["marquee"] = bool(marquee)
    if marquee_duration is not None:
        data["marquee_duration"] = int(marquee_duration)
    _save(data)
