# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

_version_namespace = {}
exec((Path('src') / 'version.py').read_text(encoding='utf-8'), _version_namespace)
VERSION = _version_namespace['__version__']
VERSION_TUPLE = ', '.join([*VERSION.split('.'), '0'])
VERSION_FILE = Path('build') / 'version-info.generated.txt'
VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
VERSION_FILE.write_text(
    Path('packaging/version-info.txt').read_text(encoding='utf-8')
    .replace('@VERSION_TUPLE@', VERSION_TUPLE)
    .replace('@VERSION@', VERSION), encoding='utf-8'
)

block_cipher = None
datas = [
    ('src/locales', 'src/locales'),
    ('resources', 'resources'),
    ('namelist模板.xls', '.'),
]
binaries = []
hiddenimports = []

a = Analysis(
    ['src/main.py'], pathex=['src'], binaries=binaries, datas=datas,
    hiddenimports=hiddenimports, hookspath=[], hooksconfig={},
    excludes=[], cipher=block_cipher, noarchive=False,
)
if sys.platform == 'win32':
    # The Codex build PATH can expose Poppler's ICU78 DLLs. They are ABI
    # incompatible with Qt's system ICU resolution and must not enter the EXE.
    a.binaries = [
        item for item in a.binaries
        if Path(item[0]).name.casefold() not in {'icuuc.dll', 'icudt78.dll'}
    ]
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(
        pyz, a.scripts, [], [], [], [],
        name='RollCall', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False, target_arch='arm64',
        exclude_binaries=True,
    )
    collected = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='RollCall')
    app = BUNDLE(
        collected, name='RollCall.app', bundle_identifier='com.charlotterunrun.rollcall',
        info_plist={
            'CFBundleDisplayName': 'RollCall',
            'CFBundleShortVersionString': VERSION,
            'CFBundleVersion': VERSION,
            'LSMinimumSystemVersion': '15.0',
            'NSHighResolutionCapable': True,
        },
    )
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='RollCall', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False,
        version=str(VERSION_FILE),
    )
