# RollCall v2.1.0 实机验收清单 / Manual acceptance checklist

Use a copied binary in a fresh temporary data folder. Use fictional students only and record the device, OS version, binary SHA-256, date, and result. Do not open or modify a real attendance workbook during this check.

在独立临时数据目录中使用复制出的 v2.1.0 程序。只导入虚构学生，并记录设备、系统版本、程序 SHA-256、日期和结果。验收期间不要打开或修改真实考勤工作簿。

1. [ ] Download and open the ordinary Windows 11 x64 unsigned EXE, or the macOS 15+ Apple Silicon ARM64 ad-hoc signed, unnotarized ZIP. 下载并打开普通的 Windows 11 x64 未签名 EXE，或 macOS 15+ Apple Silicon ARM64 ad-hoc 签名、未公证 ZIP。
2. [ ] Confirm the normal 640x480 window is usable; on an old PC or short/small screen, confirm controls are visible or vertically reachable by scrolling. 确认普通 640x480 窗口可用；在旧电脑或较短的小屏上确认控件可见，或可通过纵向滚动到达。
3. [ ] Toggle both languages, Chinese and English, once and confirm the current student, timer, progress, and checkbox state stay unchanged. 切换两种语言（中文和 English）一次，确认当前学生、计时器、进度和勾选状态不变。
4. [ ] Check **End this roll call session** / **本次点名结束**, record one synthetic student, and confirm the save succeeds before exactly one session-ended dialog appears. 勾选“本次点名结束”，记录一名虚构学生，确认先成功保存，再只出现一个结束对话框。
5. [ ] Click **OK** / **确定** and confirm the app exits; reopen it and confirm the remaining students resume from the workbook. 点击“确定”并确认程序退出；重新打开后确认从工作簿继续剩余学生。
6. [ ] If time permits, lock the workbook during a save and make one manual backup/restore check; record unavailable devices or failed steps with a reason. 如时间允许，在保存时锁定工作簿并做一次手工备份/恢复检查；无法使用的设备或失败步骤要写明原因。

Automated packaged smoke evidence does not count as visible desktop acceptance. 自动打包 smoke 不能替代可见桌面验收。
