# Changelog

## v2.0.0 — current upgrade

### Added

- Daily progress now excludes every student with a valid attendance entry for the current date, and the day finishes once all students have an entry.
- Four explicit strategies: random/sequence, each with or without balancing other-date attendance counts.
- Optional marquee selection with a configurable 100–10,000 ms stop duration.
- Chinese and English interface language choices, matching blank Excel templates, and storage-language preservation for existing workbooks.
- Crash-resistant `.xlsx` writes, conflict detection, automatic backups, permanent upgrade/manual/pre-restore snapshots, restore, import, and data-folder recovery flows.
- Windows 11 x64 single-file packaging and macOS 15+ Apple Silicon ARM64 application ZIP packaging.

### Fixed

- A student already recorded today is skipped across all strategies and cannot receive a second attendance entry for that date.
- Failed saves preserve the previous workbook and their backup evidence; automatic cleanup runs only after a successful save and retains the newest 50 automatic backups.
- Invalid Excel headers, dates, statuses, formulas, merged key areas, duplicate IDs, duplicate dates, ambiguous worksheets, and external edits are rejected with recovery-oriented errors.
- Switching language or crossing midnight preserves the live session safely and reloads the current workbook before further attendance.

### Compatibility

- Existing v1 `.xlsx` record workbooks can be opened or imported. The first v2 write creates a permanent upgrade snapshot keyed to the old bytes; manual and pre-restore snapshots are also retained.
- Roster import accepts `.xlsx` and legacy `.xls`. Record storage is `.xlsx`.
- v2 keeps the v1.0.0 release and its assets as a separate baseline; it does not overwrite that release.

## v1.0.0 — original baseline

- Original Windows classroom roll-call release, preserved as the byte-identical public baseline asset.
- Basic roster import, roll-call recording, and workbook storage.
- The v1 release remains available from the [v1.0.0 GitHub release](https://github.com/charlotterunrun-bot/RollCall/releases/tag/v1.0.0).
