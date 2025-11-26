#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Build Script
PyInstaller configuration for Professional Accounting ERP
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_directories():
    """Clean previous build directories"""
    try:
        dirs_to_clean = ['build', 'dist', '__pycache__']
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                print(f"Cleaned {dir_name}")

        # Clean all __pycache__ directories
        for root, dirs, files in os.walk('.'):
            for dir_name in dirs:
                if dir_name == '__pycache__':
                    shutil.rmtree(os.path.join(root, dir_name))

        print("Build directories cleaned successfully")

    except Exception as e:
        print(f"Error cleaning build directories: {e}")


def create_spec_file():
    """Create PyInstaller spec file"""
    try:
        spec_content = r"""# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Application metadata
app_name = "ProfessionalAccountingERP"

# Use project root as pathex
project_root = Path(".").resolve()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('lang', 'lang'),
        ('assets', 'assets'),
        ('templates', 'templates'),
        ('database', 'database'),
    ],
    hiddenimports=[
        'tkinterdnd2',
        'PIL.ImageTk',
        'matplotlib.backends.backend_tkagg',
        'customtkinter',
        'bcrypt',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico',
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
"""

        with open('app.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)

        print("PyInstaller spec file created: app.spec")

    except Exception as e:
        print(f"Error creating spec file: {e}")


def create_version_info():
    """Create version info file for Windows (used by EXE in spec)"""
    try:
        version_info = r"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'Accounting ERP Solutions'),
            StringStruct('FileDescription', 'Professional Accounting ERP System'),
            StringStruct('FileVersion', '1.0.0'),
            StringStruct('InternalName', 'ProfessionalAccountingERP'),
            StringStruct('LegalCopyright', 'Copyright © 2024 Accounting ERP Solutions'),
            StringStruct('OriginalFilename', 'ProfessionalAccountingERP.exe'),
            StringStruct('ProductName', 'Professional Accounting ERP'),
            StringStruct('ProductVersion', '1.0.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', 1033, 1200)])
  ]
)
"""

        with open('version_info.txt', 'w', encoding='utf-8') as f:
            f.write(version_info)

        print("Version info file created: version_info.txt")

    except Exception as e:
        print(f"Error creating version info: {e}")


def create_app_icon():
    """Create simple app icon placeholder"""
    try:
        # Create assets directory if it doesn't exist
        os.makedirs('assets', exist_ok=True)

        # Icon path used by spec
        icon_path = 'assets/app_icon.ico'
        if os.path.exists(icon_path):
            print(f"Icon already exists: {icon_path}")
            return

        # Create a simple placeholder icon using PIL
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create a simple 64x64 image
            img = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)

            # Draw circle
            draw.ellipse([8, 8, 56, 56], outline=(0, 100, 200, 255), width=3)

            # Draw simple currency sign
            text = "€"
            font = ImageFont.load_default()
            w, h = draw.textsize(text, font=font)
            draw.text(((64 - w) / 2, (64 - h) / 2), text, fill=(0, 100, 200, 255), font=font)

            # Save as ICO
            img.save(icon_path, 'ICO', sizes=[(64, 64)])
            print(f"Created placeholder icon: {icon_path}")

        except ImportError:
            print("PIL not available, creating empty icon file placeholder")
            # Create a simple empty file so PyInstaller doesn't fail
            with open(icon_path, 'wb') as f:
                f.write(b'')

    except Exception as e:
        print(f"Error creating app icon: {e}")


def create_installer():
    """Create NSIS installer for Windows"""
    try:
        # Check if we're on Windows
        if os.name != 'nt':
            print("Skipping installer creation (not on Windows)")
            return

        nsis_script = r"""!define APPNAME "Professional Accounting ERP"
!define VERSION "1.0.0"
!define PUBLISHER "Accounting ERP Solutions"
!define DESCRIPTION "Professional Accounting ERP System"
!define INSTALLER "${APPNAME} Installer"

!include "MUI2.nsh"

Name "${APPNAME}"
OutFile "${APPNAME}_Setup_${VERSION}.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "InstallPath"
RequestExecutionLevel admin

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Arabic"

Section "Core Files" SecCore
    SectionIn RO
    SetOutPath "$INSTDIR"
    File /r "dist\ProfessionalAccountingERP\*"

    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\ProfessionalAccountingERP.exe"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\ProfessionalAccountingERP.exe"

    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\ProfessionalAccountingERP.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${PUBLISHER}"
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\ProfessionalAccountingERP.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\${APPNAME}\*.*"
    RMDir "$SMPROGRAMS\${APPNAME}"
    Delete "$DESKTOP\${APPNAME}.lnk"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
"""

        with open('installer.nsi', 'w', encoding='utf-8') as f:
            f.write(nsis_script)

        print("NSIS installer script created: installer.nsi")
        print("To create installer, run: makensis installer.nsi")

    except Exception as e:
        print(f"Error creating installer: {e}")


def create_license():
    """Create license file"""
    try:
        license_text = """Professional Accounting ERP - License Agreement
===============================================

This is a license agreement for the Professional Accounting ERP software.

Copyright (c) 2024 Accounting ERP Solutions

This software is provided "as-is" without any warranty.
"""

        with open('LICENSE.txt', 'w', encoding='utf-8') as f:
            f.write(license_text)

        print("License file created: LICENSE.txt")

    except Exception as e:
        print(f"Error creating license: {e}")


def build_application():
    """Build the application using PyInstaller"""
    try:
        # Check if PyInstaller is available
        try:
            import PyInstaller  # noqa: F401
        except ImportError:
            print("PyInstaller not found. Installing...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            print("PyInstaller installed successfully")

        build_cmd = [
            sys.executable,
            '-m',
            'PyInstaller',
            '--clean',
            '--noconfirm',
            '--log-level=INFO',
            'app.spec'
        ]

        print("Building application...")
        print(f"Command: {' '.join(build_cmd)}")

        result = subprocess.run(build_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("Build completed successfully!")
            print(result.stdout)

            dist_path = Path('dist')
            if dist_path.exists():
                print(f"Build artifacts created in: {dist_path.absolute()}")

                for file_path in dist_path.rglob('*'):
                    if file_path.is_file():
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        print(f"  {file_path.relative_to(dist_path)} ({size_mb:.1f} MB)")

                return True
            else:
                print("Warning: No dist directory found")
                return False
        else:
            print("Build failed!")
            print("STDOUT:\n", result.stdout)
            print("STDERR:\n", result.stderr)
            return False

    except subprocess.CalledProcessError as e:
        print(f"Build command failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during build: {e}")
        return False


def main():
    """Main build process"""
    print("=== Professional Accounting ERP Build Process ===\n")

    # Step 1: Clean previous builds
    print("Step 1: Cleaning previous build directories...")
    clean_build_directories()

    # Step 2: Create configuration files
    print("\nStep 2: Creating configuration files...")
    create_spec_file()
    create_version_info()
    create_app_icon()
    create_license()

    # Step 3: Build application
    print("\nStep 3: Building application...")
    build_success = build_application()

    if build_success:
        # Step 4: Create installer (Windows only)
        print("\nStep 4: Creating installer...")
        create_installer()

        print("\n=== Build Process Completed Successfully! ===")
        print("\nNext steps:")
        print("1. Test the application in dist/ProfessionalAccountingERP/")
        print("2. On Windows, create installer with: makensis installer.nsi")
    else:
        print("\n=== Build Process Failed! ===")
        print("Please check the error messages above and fix any issues.")


if __name__ == "__main__":
    main()
