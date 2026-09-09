"""Validated, crash resistant persistence for RollCall settings."""

from __future__ import annotations

import json
from pathlib import Path

import paths
import storage
from errors import AppError

STRATEGY_RANDOM_COUNT = "random_count"
STRATEGY_RANDOM_NO_COUNT = "random_no_count"
STRATEGY_SEQ_NO_COUNT = "seq_no_count"
STRATEGY_SEQ_COUNT = "seq_count"
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
STRATEGY_ORDER = list(STRATEGY_LABELS)

CONFIG_INVALID = "config.invalid"
CONFIG_READ_FAILED = "config.read_failed"
CONFIG_WRITE_FAILED = "config.write_failed"


def defaults() -> dict:
    return {"strategy": DEFAULT_STRATEGY, "marquee": DEFAULT_MARQUEE, "marquee_duration": DEFAULT_MARQUEE_DURATION}


def _validate(data, *, path=None) -> dict:
    target = str(path or paths.config_path())
    if not isinstance(data, dict):
        raise AppError(CONFIG_INVALID, path=target, reason="object required")
    result = dict(data)
    strategy = result.get("strategy", DEFAULT_STRATEGY)
    marquee = result.get("marquee", DEFAULT_MARQUEE)
    duration = result.get("marquee_duration", DEFAULT_MARQUEE_DURATION)
    if not isinstance(strategy, str) or strategy not in STRATEGY_LABELS:
        raise AppError(CONFIG_INVALID, path=target, field="strategy")
    if not isinstance(marquee, bool):
        raise AppError(CONFIG_INVALID, path=target, field="marquee")
    if isinstance(duration, bool) or not isinstance(duration, int) or not (MARQUEE_DURATION_MIN <= duration <= MARQUEE_DURATION_MAX):
        raise AppError(CONFIG_INVALID, path=target, field="marquee_duration")
    result.update(strategy=strategy, marquee=marquee, marquee_duration=duration)
    return result


def load_settings() -> dict:
    """Return defaults for a missing file; leave invalid bytes untouched."""
    target = Path(paths.config_path())
    if not target.exists():
        return defaults()
    try:
        with target.open("r", encoding="utf-8") as stream:
            raw = json.load(stream)
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        raise AppError(CONFIG_INVALID, path=str(target), reason="invalid JSON") from exc
    except OSError as exc:
        raise AppError(CONFIG_READ_FAILED, path=str(target)) from exc
    return _validate(raw, path=target)


def load_strategy() -> str:
    return load_settings()["strategy"]


def load_marquee() -> bool:
    return load_settings()["marquee"]


def load_marquee_duration() -> int:
    return load_settings()["marquee_duration"]


def _json_validator(candidate: Path):
    def validate(path: Path):
        try:
            with path.open("r", encoding="utf-8") as stream:
                _validate(json.load(stream), path=candidate)
        except AppError:
            raise
        except Exception as exc:
            raise AppError(CONFIG_INVALID, path=str(path)) from exc
    return validate


def save_settings(strategy=None, marquee=None, marquee_duration=None) -> dict:
    target = Path(paths.config_path())
    if target.exists():
        try:
            existing = load_settings()
        except AppError as exc:
            if exc.code != CONFIG_INVALID:
                raise
            # An explicit save is the recovery action. atomic_write captures
            # the corrupt bytes as a permanent manual backup first.
            existing = defaults()
    else:
        existing = defaults()
    candidate = dict(existing)
    if strategy is not None:
        candidate["strategy"] = strategy
    if marquee is not None:
        candidate["marquee"] = marquee
    if marquee_duration is not None:
        candidate["marquee_duration"] = marquee_duration
    candidate = _validate(candidate, path=target)
    raw = json.dumps(candidate, ensure_ascii=False, indent=2).encode("utf-8")

    def writer(temp):
        temp.write_bytes(raw)

    try:
        storage.atomic_write(
            target, writer, _json_validator(target),
            expected_fingerprint=storage.fingerprint(target), backup_kind="manual",
        )
    except AppError:
        raise
    except Exception as exc:
        raise AppError(CONFIG_WRITE_FAILED, path=str(target)) from exc
    return candidate
