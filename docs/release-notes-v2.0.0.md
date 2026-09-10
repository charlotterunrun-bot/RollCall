# RollCall v2.0.0

## 中文说明

RollCall v2 brings daily attendance protection, four selection strategies, Chinese and English interfaces, and recoverable Excel storage to the classroom roll-call workflow. Students with a valid entry for the current calendar date are skipped, and a completed day cannot start a second round.

本版本还包括走马灯选择、`.xlsx` 安全写入、冲突检测、自动备份（成功保存后保留最近 50 份）、升级快照、手工备份、恢复和旧版工作簿导入。切换界面语言只翻译界面，不重新抽选或重置进度。详情见 [中文说明](../README.md) 和 [English guide](../README.en.md)。

下载资产：

- `RollCall-2.0.0-Windows-x64.exe`：Windows 11 x64 单文件程序，当前未签名。
- `RollCall-2.0.0-macOS-arm64.zip`：macOS 15+ Apple Silicon ARM64 应用，ad-hoc 签名、未经过 Apple 公证。
- `SHA256SUMS.txt`：两个平台资产的 SHA-256 校验值。

v1.0.0 发布及资产继续作为独立基线保留。升级前请保留原有 `record.xlsx` 副本；v2 首次写入旧工作簿时会创建永久升级快照。公开仓库和发布资产不包含真实名单、考勤记录、配置、备份或凭据。

自动发布验收要求 Windows 和 macOS 原生测试、实际打包、平台架构检查、签名检查（macOS）以及打包程序离屏 smoke 全部成功。当前没有手动 Mac 桌面验收；Windows 可见桌面点击也必须以实际设备清单结果为准，不能用自动 smoke 替代。macOS 包未公证，首次打开可能需要在“隐私与安全性”中允许。

## English

RollCall v2 adds daily attendance protection, four selection strategies, Chinese and English interfaces, and recoverable Excel storage. Students with a valid entry for the current calendar date are skipped, and a completed day cannot start a second round.

The release also includes optional marquee selection, safe `.xlsx` writes, conflict detection, automatic backups (the newest 50 are retained after successful saves), upgrade snapshots, manual backup, restore, and legacy workbook import. Changing the interface language translates the UI without reselecting a student or resetting progress. See the [English guide](../README.en.md) and [Chinese guide](../README.md).

Downloads:

- `RollCall-2.0.0-Windows-x64.exe`: single-file Windows 11 x64 application; unsigned.
- `RollCall-2.0.0-macOS-arm64.zip`: macOS 15+ Apple Silicon ARM64 application; ad-hoc signed and not notarized by Apple.
- `SHA256SUMS.txt`: SHA-256 checksums for both platform assets.

The v1.0.0 release and its assets remain a separate baseline. Keep a copy of the existing `record.xlsx` before upgrading; v2 creates a permanent upgrade snapshot before its first write to a legacy workbook. The public repository and release assets contain no real rosters, attendance records, configuration, backups, or credentials.

Automated release acceptance requires native Windows and macOS tests, actual packaging, architecture checks, macOS signature verification, and packaged off-screen smoke checks to succeed. Manual Mac desktop acceptance is currently unavailable; visible Windows desktop results must come from the real-device checklist and cannot be substituted by automated smoke. The macOS package is not notarized, so first launch may require allowing it under Privacy & Security.
