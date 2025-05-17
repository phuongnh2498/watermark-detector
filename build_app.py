import os
import sys
import platform
import subprocess


def build_executable():
    """Build the executable for the current platform"""
    print(f"Building executable for {platform.system()}...")

    # Create a spec file with additional options
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

import sys
block_cipher = None

a = Analysis(
    ['watermark_detector_app.py'],
    pathex=[],
    binaries=[],
    datas=[('watermark_detector.pth', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WatermarkDetector',
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
    icon='app_icon.ico' if sys.platform == 'win32' else 'app_icon.icns',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='WatermarkDetector.app',
        icon='app_icon.icns',
        bundle_identifier=None,
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'CFBundleName': 'Watermark Detector',
            'CFBundleDisplayName': 'Watermark Detector',
            'CFBundleGetInfoString': 'Watermark Detector',
            'CFBundleIdentifier': 'com.watermarkdetector.app',
            'NSRequiresAquaSystemAppearance': 'False',
        },
    )
"""

    # Write the spec file
    with open("WatermarkDetector.spec", "w") as f:
        f.write(spec_content)

    # Determine the PyInstaller command based on the platform
    cmd = ["pyinstaller", "WatermarkDetector.spec"]

    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print("Build completed successfully!")

        # Print the location of the executable
        if platform.system() == "Darwin":
            print("Executable location: dist/WatermarkDetector.app")
        elif platform.system() == "Windows":
            print("Executable location: dist/WatermarkDetector.exe")

    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")


if __name__ == "__main__":
    build_executable()
