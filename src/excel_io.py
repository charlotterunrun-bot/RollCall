"""Excel reading / writing for the roll-call record and namelist import."""
import os

from openpyxl import Workbook, load_workbook
import xlrd

import paths

HEADERS = ["序号", "学号", "姓名", "班级"]


def _fmt(value):
    """Normalize a cell value to a clean string."""
    if value is None:
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    return str(value).strip()


def _to_int(value):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


class Student:
    __slots__ = ("row", "seq", "seq_num", "no", "name", "clazz", "records")

    def __init__(self, row, seq, no, name, clazz, records=None):
        self.row = row            # 1-based row index in record.xlsx
        self.seq = seq            # raw 序号 string
        self.seq_num = _to_int(seq)
        self.no = no              # 学号 string
        self.name = name
        self.clazz = clazz
        self.records = records or {}   # date -> "到"/"假"/"旷"

    @property
    def id(self):
        return self.no


class RollCallData:
    def __init__(self, students, date_columns):
        self.students = students
        self.date_columns = date_columns


def is_first_run() -> bool:
    if not os.path.isfile(paths.record_path()):
        return True
    try:
        data = load_record()
    except Exception:
        return True
    return len(data.students) == 0


def load_record() -> RollCallData:
    wb = load_workbook(paths.record_path(), data_only=True)
    try:
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()

    if not rows:
        return RollCallData([], [])

    header = [_fmt(c) for c in rows[0]]
    date_columns = [c for c in header[4:] if c]

    students = []
    for idx, r in enumerate(rows[1:], start=2):
        if not r or all((c is None or str(c).strip() == "") for c in r):
            continue
        seq = _fmt(r[0]) if len(r) > 0 else ""
        no = _fmt(r[1]) if len(r) > 1 else ""
        name = _fmt(r[2]) if len(r) > 2 else ""
        clazz = _fmt(r[3]) if len(r) > 3 else ""
        records = {}
        for j, d in enumerate(date_columns):
            val = r[4 + j] if len(r) > 4 + j else None
            if val is not None and str(val).strip():
                records[d] = str(val).strip()
        students.append(Student(idx, seq, no, name, clazz, records))

    return RollCallData(students, date_columns)


def read_namelist(path) -> list:
    """Read + strictly validate a namelist file. Returns list of dicts."""
    if path.lower().endswith(".xls"):
        return _read_namelist_xls(path)
    return _read_namelist_xlsx(path)


def _read_namelist_xlsx(path) -> list:
    wb = load_workbook(path, data_only=True, read_only=True)
    try:
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()
    return _parse_namelist_rows(rows)


def _read_namelist_xls(path) -> list:
    book = xlrd.open_workbook(path)
    sheet = book.sheet_by_index(0)
    rows = []
    for r in range(sheet.nrows):
        rows.append([sheet.cell_value(r, c) for c in range(sheet.ncols)])
    return _parse_namelist_rows(rows)


def _parse_namelist_rows(rows) -> list:
    if not rows:
        raise ValueError("花名册文件为空")

    header = [_fmt(c) for c in rows[0][:4]]
    if header != HEADERS:
        raise ValueError(
            "表头必须为「序号 / 学号 / 姓名 / 班级」四列，\n实际读取到：" + " / ".join(header) or "（空）"
        )

    students = []
    seen = set()
    for idx, r in enumerate(rows[1:], start=2):
        if not r or all((c is None or str(c).strip() == "") for c in r):
            continue
        seq = _fmt(r[0]) if len(r) > 0 else ""
        no = _fmt(r[1]) if len(r) > 1 else ""
        name = _fmt(r[2]) if len(r) > 2 else ""
        clazz = _fmt(r[3]) if len(r) > 3 else ""

        if not no:
            raise ValueError(f"第 {idx} 行学号为空")
        if not name:
            raise ValueError(f"第 {idx} 行姓名为空")
        if no in seen:
            raise ValueError(f"学号重复：{no}（第 {idx} 行）")
        seen.add(no)
        students.append({"seq": seq, "no": no, "name": name, "clazz": clazz})

    if not students:
        raise ValueError("花名册中没有学生信息")
    return students


def create_record_from_namelist(students) -> None:
    os.makedirs(paths.record_dir(), exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "record"
    ws.append(HEADERS)
    for s in students:
        ws.append([s["seq"], s["no"], s["name"], s["clazz"]])
    wb.save(paths.record_path())
    wb.close()


def write_record(no: str, date: str, value: str) -> None:
    """Write a value into the given date column for the student with 学号 `no`."""
    path = paths.record_path()
    wb = load_workbook(path)
    try:
        ws = wb.active
        headers = [c.value for c in ws[1]]
        col = None
        for i, h in enumerate(headers):
            if h is not None and str(h).strip() == date:
                col = i + 1
                break
        if col is None:
            col = len(headers) + 1
            ws.cell(row=1, column=col, value=date)

        row = None
        for r in range(2, ws.max_row + 1):
            if _fmt(ws.cell(row=r, column=2).value) == no:
                row = r
                break
        if row is None:
            raise ValueError(f"未找到学号 {no}")

        ws.cell(row=row, column=col, value=value)
        wb.save(path)
    finally:
        wb.close()
