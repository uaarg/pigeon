# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['pigeon/__main__.py', 'pigeon/comms/__init__.py', 'pigeon/comms/services/__init__.py', 'pigeon/comms/services/command.py', 'pigeon/comms/services/common.py', 'pigeon/comms/services/imagesservice.py', 'pigeon/comms/uav.py', 'pigeon/features.py', 'pigeon/geo.py', 'pigeon/image.py', 'pigeon/log.py', 'pigeon/misc/__init__.py', 'pigeon/misc/qr.py', 'pigeon/settings.py', 'pigeon/ui/__init__.py', 'pigeon/ui/areas/__init__.py', 'pigeon/ui/areas/commandsarea.py', 'pigeon/ui/areas/controlsarea.py', 'pigeon/ui/areas/messagelogarea.py', 'pigeon/ui/areas/featuredetailarea.py', 'pigeon/ui/areas/infoarea.py', 'pigeon/ui/areas/imagemaparea.py', 'pigeon/ui/areas/ruler.py', 'pigeon/ui/areas/settingsarea.py', 'pigeon/ui/areas/thumbnailarea.py', 'pigeon/ui/common.py', 'pigeon/ui/commonwidgets.py', 'pigeon/ui/dialogues/__init__.py', 'pigeon/ui/dialogues/qr.py', 'pigeon/ui/icons.py', 'pigeon/ui/pixmaploader.py', 'pigeon/ui/style.py', 'pigeon/ui/ui.py'],
    pathex=[],
    binaries=[],
    datas=[('data/icons/', 'data/icons'), ('data/ground_control_points.json', 'data/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pigeon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='pigeon.app',
    icon=None,
    bundle_identifier=None,
)
