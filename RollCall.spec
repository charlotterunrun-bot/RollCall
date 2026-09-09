# -*- mode: python ; coding: utf-8 -*-
import sys

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
    runtime_hooks=['packaging/pyside6-runtime-hook.py'],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='RollCall', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False, target_arch='arm64',
    )
    app = BUNDLE(
        exe, name='RollCall.app', bundle_identifier='com.charlotterunrun.rollcall',
        info_plist={
            'CFBundleDisplayName': 'RollCall',
            'CFBundleShortVersionString': '2.0.0',
            'CFBundleVersion': '2.0.0',
            'LSMinimumSystemVersion': '15.0',
            'NSHighResolutionCapable': True,
        },
    )
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='RollCall', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False,
        version='packaging/version-info.txt',
    )
