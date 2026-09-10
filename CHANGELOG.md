# Changelog

## v2.1.0 — session control and compact screens

### v2.1.0 中文摘要

v2.1.0 增加两项点名体验改进：可选的“本次点名结束”勾选项会在成功保存当前学生后显示一次结束提示，确认后退出，重新启动可从工作簿继续剩余学生；启动窗口在普通屏幕使用可调整的 640x480 默认客户区，在较短的小屏上自动适配并支持滚动以保持底部控件可达。每日完成规则、`record.xlsx` 数据格式和备份行为保持不变。

### v2.1.0 English summary

v2.1.0 adds two user-facing improvements: an optional **End this roll call session** checkbox saves the current student before showing one end-of-session dialog and closing after confirmation, while the next launch continues with remaining students; the startup window keeps a resizable 640x480 default client area and fits or scrolls on short screens so bottom controls remain reachable. Daily completion rules, the `record.xlsx` data format, and backup behavior are unchanged.

## v2.0.0 — current upgrade

### v2.0.0 中文摘要

v2.0.0 在保留 v1.0.0 基线的基础上，加入每日每名学生最多一条记录、当天完成后不再开启第二轮、随机/按序与计重复/不计重复四种组合规则、可配置走马灯，以及中英文界面和 Excel 存储语言。版本还加入冲突检测、成功保存后仅保留最新 50 份自动备份、永久升级/手工/恢复前快照、恢复与旧记录导入，并提供 Windows 11 x64 EXE 与 macOS 15+ Apple Silicon ARM64 ZIP。已有 v1 `.xlsx` 记录可直接打开或导入，v1.0.0 发布和资产继续独立保留。

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

### v1.0.0 中文摘要

v1.0.0 是最初的 Windows 课堂点名基线版本，支持花名册导入、点名记录和 Excel 存储。该版本的公开发布和资产作为原始基线继续保留，不被 v2.0.0 覆盖。

- Original Windows classroom roll-call release, preserved as the byte-identical public baseline asset.
- Basic roster import, roll-call recording, and workbook storage.
- The v1 release remains available from the [v1.0.0 GitHub release](https://github.com/charlotterunrun-bot/RollCall/releases/tag/v1.0.0).
