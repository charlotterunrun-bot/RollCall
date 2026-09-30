# RollCall · 课堂点名

**中文**：RollCall 是一款面向课堂的极简桌面点名工具——单文件、免安装、数据本地保存。教师可随机或按序抽取学生并记录考勤，支持多天累计与人工纠错。

**English**: RollCall is a minimal classroom roll-call desktop tool — single-file, install-free, local data. Teachers pick students randomly or in sequence and record attendance, with multi-day accumulation and manual-correction tolerance.

---

## 设计目的 · Design Purpose

**中文**：为教师提供"打开即用、零配置"的点名工具，把随机/按序抽人、考勤记录、多天累计、人工纠错等重复工作收敛到一个本地小程序；不依赖网络与云服务，数据保存在运行目录，可随时用 Excel 查看与修正。

**English**: Give teachers an open-and-use, zero-config roll-call tool that folds repetitive work — random/sequential picking, attendance recording, multi-day accumulation, and manual correction — into one local utility. No network or cloud required; data stays in the run directory and can be reviewed or fixed in Excel anytime.

## 设计思路 · Design Philosophy

**中文**：
- 极简交付：单文件程序，自带全部运行库，免安装。
- 分层架构：表现层（UI）/ 业务逻辑（规则）/ 数据（Excel 读写）分离，便于测试与扩展。
- 策略模式：四种点名规则统一为"下一名点谁"的策略，配置化切换。
- 本地优先：考勤写 `record.xlsx`、设置写 `config.json`；崩溃安全（原子写 + 备份 + 恢复）。
- 表现与逻辑解耦：走马灯动画滚动的是完整名单，真正被选中的学生由策略决定，互不干扰。

**English**:
- Minimal delivery: a single-file program bundling all runtime; no install.
- Layered architecture: UI / business rules / data (Excel) are separated for testing and extension.
- Strategy pattern: the four rules collapse into one "who's next" strategy, switched via configuration.
- Local first: attendance to `record.xlsx`, settings to `config.json`; crash-safe (atomic write + backup + restore).
- Presentation vs logic decoupled: the marquee scrolls the full roster, while the actual pick is decided by the strategy.

## 主要功能 · Key Features

**中文**：
- 单文件免安装（Windows x64 / macOS ARM64）。
- 花名册导入与校验（`.xlsx` / `.xls`，表头、学号、姓名、重复校验）。
- 四种点名规则：随机 / 按序号 × 计重复 / 不计重复。
- 走马灯抽选动画（可开关、可调自动停下时长）。
- 考勤写入 Excel 日期列（`YYYY-MM-DD`），多天累计；当天已记录学生自动跳过。
- 人工纠错容忍（v2.2）：历史与当天的非标准标记（如"迟到"）仅提醒一次并记日志，不影响使用；仅未来日期的人工数据报错并给出详细信息。
- 中英双语界面，可切换并持久化。
- 崩溃安全存储：原子写入、多级备份、恢复；会话锁、启动恢复、数据目录可配置。

**English**:
- Single-file, install-free (Windows x64 / macOS ARM64).
- Roster import and validation (`.xlsx` / `.xls`; headers, student ID, name, duplicates).
- Four roll-call rules: random / sequence × balance / no-balance.
- Marquee selection animation (toggleable, adjustable auto-stop duration).
- Attendance written into Excel date columns (`YYYY-MM-DD`), accumulated across days; students already recorded today are skipped.
- Manual-correction tolerance (v2.2): non-standard marks (e.g. "late") on past and today's records only raise a one-time notice plus a log entry; only future-date manual data errors, with details.
- Bilingual UI (Chinese / English), switchable and persisted.
- Crash-safe storage: atomic writes, tiered backups, restore; session lock, startup recovery, configurable data directory.

## 版本更新历史 · Version History

| 版本 | 日期 | 主要变更 |
|---|---|---|
| v2.2.0 | 2026-09-30 | 容忍人工改动的出勤标记：历史/当天仅提醒 + 日志，未来日期报错并给出详细信息 |
| v2.1.0 | 2026-09-10 | 新增"本次点名结束"会话控制；小屏窗口自适应与滚动 |
| v2.0.0 | 2026-09-10 | 四种规则、走马灯、中英双语、崩溃安全存储/备份/恢复、多平台打包 |
| v1.0.0 | 2026-09-09 | 基线：单文件点名 + 考勤记录 |

| Version | Date | Changes |
|---|---|---|
| v2.2.0 | 2026-09-30 | Tolerate hand-edited attendance marks: past/today → notice + log; future → error with details |
| v2.1.0 | 2026-09-10 | "End this roll call session" control; compact-screen window fit and scrolling |
| v2.0.0 | 2026-09-10 | Four rules, marquee, bilingual UI, crash-safe storage/backup/restore, multi-platform packaging |
| v1.0.0 | 2026-09-09 | Baseline: single-file roll call + attendance recording |

---

**下载 · Download**：请见 [Releases](https://github.com/charlotterunrun-bot/RollCall/releases)。

**更多细节 · More details**：见 [CHANGELOG.md](CHANGELOG.md)。
