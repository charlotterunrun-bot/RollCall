# RollCall v2.0.0 实机验收清单 / Manual acceptance checklist

Use a copied binary in a fresh temporary data folder. Use fictional students only and record the device, OS version, binary SHA-256, date, and result. Do not open or modify a real attendance workbook during this check.

在独立临时数据目录中使用复制出的程序。只导入虚构学生，并记录设备、系统版本、程序 SHA-256、日期和结果。验收期间不要打开或修改真实考勤工作簿。

- [ ] Download and open the Windows 11 x64 unsigned EXE, or the macOS 15+ Apple Silicon ARM64 ad-hoc signed, unnotarized ZIP. 下载并打开 Windows 11 x64 未签名 EXE，或 macOS 15+ Apple Silicon ARM64 ad-hoc 签名、未公证 ZIP。
- [ ] Switch between both languages before and during selection; confirm the selected student, timer, and progress stay unchanged. 在两种语言之间切换，确认当前学生、计时器和进度不变。
- [ ] Import a fictional roster and confirm the blank template and workbook language. 导入虚构学生花名册，确认空模板和工作簿语言。
- [ ] Record all three statuses: Present/到, Leave/假, and Absent/旷. 依次测试三种状态。
- [ ] Close and reopen during the day; confirm the current workbook resumes, then complete the day and confirm a second round cannot start. 当天关闭并重开，确认续点；完成当天后确认不能开始第二轮。
- [ ] Attempt a save while the workbook is exclusively locked; confirm an actionable error appears and the current student and file bytes remain unchanged until retry. 模拟文件占用，确认错误可理解，当前学生和文件字节在重试前不变。
- [ ] Create a manual backup, restore it, and confirm the restored student and attendance cells. 创建手工备份并恢复，确认学生和考勤单元格。
- [ ] Close the application and open `record.xlsx` in Excel or a compatible viewer; confirm the expected headers, dates, and statuses. 关闭程序后用 Excel 或兼容查看器打开 `record.xlsx`，确认表头、日期和状态。
- [ ] Record unavailable devices or failed steps as pending with a reason; automated packaged smoke evidence does not count as visible desktop acceptance. 无法使用的设备或失败步骤要写明原因；自动打包 smoke 不能替代可见桌面验收。
