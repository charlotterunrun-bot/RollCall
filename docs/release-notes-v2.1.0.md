# RollCall v2.1.0

## 中文说明

v2.1.0 面向 Windows 11 x64 和 macOS 15+ Apple Silicon（ARM64），提供以下两项改进：

- 可选勾选“本次点名结束”。提交时先成功写入当前学生，再显示一次结束提示；点击“确定”后退出。重新打开程序会按当前 `record.xlsx` 继续剩余学生。
- 启动窗口在普通屏幕使用可调整的 640x480 默认客户区；可用高度较短时自动适配并允许滚动，保持底部控件可达。

每日完成规则、`record.xlsx` 数据格式和备份行为与 v2.0.0 保持不变。资产为 `RollCall-2.1.0-Windows-x64.exe`（Windows 11 x64）和 `RollCall-2.1.0-macOS-arm64.zip`（macOS 15+ Apple Silicon ARM64），另附 `SHA256SUMS.txt`。Windows 程序当前未签名；macOS 应用使用 ad-hoc 签名，未经过 Apple 公证。

截至本文档编写，v2.1.0 候选资产尚无新的原生桌面手动验收结论。自动证据边界是仓库测试、原生 CI 测试/打包、平台架构检查、macOS ad-hoc 签名检查和打包程序离屏 smoke；离屏 smoke 不等于可见桌面点击验收。Windows 和 macOS 的可见桌面验收应按清单在对应设备上完成；没有 Mac 设备时不得声称已完成手动 Mac 验收。

## English

RollCall v2.1.0 targets Windows 11 x64 and macOS 15+ Apple Silicon (ARM64) and adds two user-facing improvements:

- An optional **End this roll call session** checkbox saves the current student successfully, shows one session-ended dialog, and closes after **OK**. Reopening the app continues with remaining students from the current `record.xlsx`.
- The startup window keeps a resizable 640x480 default client area on ordinary screens and fits or scrolls on short screens so the bottom controls remain reachable.

Daily completion rules, the `record.xlsx` data format, and backup behavior are unchanged from v2.0.0. Assets are `RollCall-2.1.0-Windows-x64.exe` for Windows 11 x64 and `RollCall-2.1.0-macOS-arm64.zip` for macOS 15+ Apple Silicon ARM64, with `SHA256SUMS.txt`. The Windows executable is unsigned; the macOS app is ad-hoc signed and not notarized by Apple.

At the time of writing, v2.1.0 has no new native desktop manual acceptance result. Automated evidence covers repository tests, native CI tests and packaging, platform architecture checks, macOS ad-hoc signature checks, and packaged off-screen smoke; off-screen smoke is not visible desktop click acceptance. Visible desktop acceptance should be completed on the corresponding devices using the checklist. If no Mac device is available, no manual Mac acceptance claim should be made.
