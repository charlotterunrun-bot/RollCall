# RollCall classroom attendance

RollCall is a small desktop roll-call tool for Windows 11 x64 and macOS 15 or later on Apple Silicon (ARM64). It is distributed as a self-contained Windows executable or a macOS application ZIP.

简体中文说明见 [README.md](README.md)。

## Download

- Windows 11 x64: [v2.1.0 release assets](https://github.com/charlotterunrun-bot/RollCall/releases/tag/v2.1.0), asset name `RollCall-2.1.0-Windows-x64.exe`.
- macOS 15+ Apple Silicon: [v2.1.0 release assets](https://github.com/charlotterunrun-bot/RollCall/releases/tag/v2.1.0), asset name `RollCall-2.1.0-macOS-arm64.zip`.
- The [v1.0.0 baseline release](https://github.com/charlotterunrun-bot/RollCall/releases/tag/v1.0.0) remains available separately.

The Windows executable is currently unsigned. The macOS app is ad-hoc signed for package integrity and is not Apple notarized, so macOS may ask you to approve it in Privacy & Security after the first launch. The current evidence is automated native CI run [34378297463](https://github.com/charlotterunrun-bot/RollCall/actions/runs/34378297463): Windows tests, an actual packaged Windows off-screen smoke run, macOS ARM64 tests, an actual packaged macOS off-screen smoke run, bundle architecture checks, and ad-hoc signature verification passed there. Windows 11 x64 was also exercised with an actual executable off-screen. There has been no manual Mac desktop acceptance, and visible Windows desktop clicking remains pending because the available display automation reported no monitor.

## First launch

1. Download the asset for your platform and put it in a folder of its own.
2. On the first launch, click **Download template**. The template follows the current interface language. Fill its four columns in Excel: `No.` / `Student ID` / `Name` / `Class`.
3. Click **Choose roster file** and select the completed `.xlsx` or legacy `.xls` roster. RollCall validates the headers, student IDs, names, and duplicate IDs before creating `record.xlsx`.
4. Click **Start roll call**. Choose **Present**, **Leave**, or **Absent** for each student.

Each student can have at most one attendance entry per calendar day. A student with any valid entry in today's date column is skipped. When every student has an entry for today, the day is complete and the application does not start a complete second round on that day. Progress is read from the current workbook: restoring an older workbook or manually removing today's entries changes what remains to be recorded.

If the marquee is enabled, names and IDs scroll briefly and stop after the configured duration before the attendance buttons become available. Language changes only translate the interface and preserve the current student, timers, and progress.

The bottom row includes an optional **End this roll call session** checkbox. When checked, the current student is saved successfully before one session-ended dialog appears; choosing **OK** then closes the application. The next launch continues with the remaining students from the workbook. Normal screens use a resizable 640x480 client area; on short or small screens the window fits automatically and can scroll so the bottom controls remain reachable.

## Four selection strategies

Open **Settings → Roll-call rules…** to choose one:

- **Random — balance historical attendance counts**: choose randomly from students not recorded today, preferring the smallest count of nonempty attendance entries on other dates. Every valid status counts once, including Present, Leave, and Absent.
- **Random — do not balance historical counts**: choose randomly from students not recorded today and ignore other-date counts.
- **Sequence — do not balance historical counts**: follow roster sequence order among students not recorded today and ignore other-date counts.
- **Sequence — balance historical attendance counts**: prefer the smallest other-date count, then follow roster sequence order.

In all four strategies, every student already recorded today is excluded. The marquee can be enabled or disabled; its automatic stop duration accepts an integer from 100 to 10,000 milliseconds and defaults to 500 milliseconds.

## Language and Excel storage

The **Settings → Language** menu switches the interface between 简体中文 and English. The choice is saved in `config.json`; switching it does not reselect a student, write attendance, or reset progress. New templates use the selected language. A new record uses Chinese headers and statuses (`到`, `假`, `旷`) for Chinese, or English headers and statuses (`Present`, `Leave`, `Absent`) for English. When an existing workbook is loaded, its headers and existing statuses determine the storage language for later writes. Both language aliases are accepted when reading valid status cells.

The record workbook has four student columns followed by ISO date columns (`YYYY-MM-DD`). Keep one date column per date and one student row per student. `record.xlsx` is the live record; `config.json` stores the four strategy/marquee settings and language.

## Data folder and backups

On Windows, source launches and the Windows executable use `RollCallRecord` beside the executable or current launch directory. On macOS packaged builds, the default is `~/Library/Application Support/RollCall/RollCallRecord`. If the default folder cannot be written, startup lets you choose another folder for the current run; use **File → Open data folder** to inspect the active location. The alternate choice is not promised to persist across launches.

Backups are kept in the hidden `.rollcall-backups` directory beside `record.xlsx`.

- An automatic backup is made before each attendance record replacement attempt. After each successful save, only the newest 50 automatic (`.auto.bak`) backups are retained.
- If a save attempt fails, its backup is retained and the automatic set can temporarily exceed 50 until a later successful save prunes it.
- Upgrade snapshots (`.upgrade.bak`), manual backups (`.manual.bak`), and pre-restore copies (`.pre_restore.bak`) are permanent and are never included in automatic cleanup.

To make a manual copy, use **File → Manual backup**. To restore, close any other RollCall instance, open **File → Restore backup…**, select a valid backup, confirm, and let RollCall validate the restored workbook. The current workbook is copied to a pre-restore backup before replacement. After a restore, review today's entries because the restored file determines the day's progress.

## Safe Excel editing and rejected files

You may edit the workbook manually while RollCall is closed. Preserve the required four headers, student rows, ISO date headers, and valid statuses. Keep student IDs unique and nonempty, keep names nonempty, and avoid formulas or merged cells in required fields and date columns. A workbook with a duplicate date, ambiguous date format, duplicate usable worksheet, missing/duplicate required header, duplicate student ID, empty ID/name, formula in a key field, merged key area, invalid status, unsupported structure, or an unreadable file is rejected and remains available for recovery. The record path accepts `.xlsx`; `.xls` is supported for roster import.

If Excel is open or another process changes the workbook, RollCall detects the conflict and asks you to reload. Do not edit the workbook while an attendance save is in progress.

## Upgrade from v1.0.0 to v2.1.0

1. Finish or stop v1 and close it. Make a separate copy of its `record.xlsx` before changing files.
2. Download the v2 asset for the platform. On Windows, place the v2 executable beside the existing `RollCallRecord` folder. On macOS, launch v2 and use its default Application Support folder, or choose the folder containing the records if prompted.
3. If v2 can read the existing workbook directly, it preserves the existing records and creates a permanent v2 upgrade snapshot before the first v2 attendance write. If the old workbook is in another location, open **File → Import existing record…**, select the old `.xlsx`, confirm replacement, and then review the imported students and today's entries.
4. Continue attendance in v2. Keep the v1 copy and its [v1.0.0 release](https://github.com/charlotterunrun-bot/RollCall/releases/tag/v1.0.0) available until the imported data has been checked.

For a Mac import specifically, copy the old `record.xlsx` to an accessible location, start v2, choose **File → Import existing record…**, select that file, confirm the replacement, and continue from the imported data. The source workbook is left untouched.

## Development and packaging

The source is in `src/`, with `src/version.py` as the single version source. The application version is `2.1.0`; the Windows file metadata is `2.1.0.0`, while the product and package version strings are `2.1.0`. Build locally with Python 3.12 and the pinned requirements:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean RollCall.spec
```

The platform scripts produce `RollCall-2.1.0-Windows-x64.exe` and `RollCall-2.1.0-macOS-arm64.zip`. Do not put real rosters, attendance, credentials, virtual environments, or temporary evidence in a public repository.
