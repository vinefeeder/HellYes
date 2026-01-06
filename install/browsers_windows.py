#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
browsers_windows.py - Windows browser native messaging host installer
Registers native messaging host for Chrome, Edge, Firefox, Brave, and other browsers
"""

import os
import sys
import json
import winreg
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding for Windows console
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def get_script_dir():
    """Get the project root directory"""
    return Path(__file__).parent.parent.absolute()

def get_native_script_path():
    """Get the path to native.py with proper Windows path format"""
    script_dir = get_script_dir()

    # On Windows, we need to call python with the native.py script
    # Create a batch file wrapper
    native_py = script_dir / "native.py"
    native_bat = script_dir / "native.bat"

    # Create the batch wrapper if it doesn't exist
    if not native_bat.exists():
        venv_python = script_dir / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = "python"  # Fallback to system python

        with open(native_bat, 'w') as f:
            f.write(f'@echo off\n"{venv_python}" "{native_py}" %*\n')

    return str(native_bat)

def build_chrome_manifest(extension_id):
    """Build manifest for Chrome-based browsers"""
    native_path = get_native_script_path()

    return {
        "name": "org.hellyes.hellyes",
        "description": "Native messaging for HellYes",
        "path": native_path,
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{extension_id}/"
        ]
    }

def build_firefox_manifest():
    """Build manifest for Firefox"""
    native_path = get_native_script_path()

    return {
        "name": "org.hellyes.hellyes",
        "description": "Native messaging for HellYes",
        "path": native_path,
        "type": "stdio",
        "allowed_extensions": [
            "hellyes@hellyes.org"
        ]
    }

def create_manifest_file(manifest_data, file_path):
    """Create manifest JSON file"""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    return file_path

def register_chrome_manifest(manifest_path):
    """Register manifest in Windows registry for Chrome"""
    try:
        key_path = r"Software\Google\Chrome\NativeMessagingHosts\org.hellyes.hellyes"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error registering Chrome: {e}")
        return False

def register_edge_manifest(manifest_path):
    """Register manifest in Windows registry for Edge"""
    try:
        key_path = r"Software\Microsoft\Edge\NativeMessagingHosts\org.hellyes.hellyes"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error registering Edge: {e}")
        return False

def register_brave_manifest(manifest_path):
    """Register manifest in Windows registry for Brave"""
    try:
        key_path = r"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\org.hellyes.hellyes"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error registering Brave: {e}")
        return False

def register_firefox_manifest(manifest_path):
    """Register manifest in Windows registry for Firefox"""
    try:
        key_path = r"Software\Mozilla\NativeMessagingHosts\org.hellyes.hellyes"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path))
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error registering Firefox: {e}")
        return False

def check_browser_installed(browser_name):
    """Check if a browser is installed by checking registry"""
    registry_paths = {
        "Chrome": [
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Google\Chrome"),
        ],
        "Edge": [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Edge"),
        ],
        "Firefox": [
            (winreg.HKEY_CURRENT_USER, r"Software\Mozilla\Mozilla Firefox"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Mozilla\Mozilla Firefox"),
        ],
        "Brave": [
            (winreg.HKEY_CURRENT_USER, r"Software\BraveSoftware\Brave-Browser"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\BraveSoftware\Brave-Browser"),
        ],
    }

    if browser_name not in registry_paths:
        return False

    for hkey, path in registry_paths[browser_name]:
        try:
            key = winreg.OpenKey(hkey, path)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            continue

    return False

def install_browsers_manifest(extension_id=None):
    """Install browser manifests for all detected browsers"""
    script_dir = get_script_dir()
    results = []

    print("=" * 60)
    print("HellYes Browser Native Messaging Host Installer (Windows)")
    print("=" * 60)
    print()

    # Check for Chrome-based browsers
    chrome_browsers = []
    if check_browser_installed("Chrome"):
        chrome_browsers.append("Chrome")
    if check_browser_installed("Edge"):
        chrome_browsers.append("Edge")
    if check_browser_installed("Brave"):
        chrome_browsers.append("Brave")

    if chrome_browsers:
        print(f"[+] Detected Chrome-based browsers: {', '.join(chrome_browsers)}")
        print()

        # Ask for extension ID
        if extension_id is None:
            print("Select Chrome extension installation type:")
            print("1) Compiled extension (default) - Official release")
            print("2) Unpacked extension - Development mode")
            print("3) Skip Chrome extension installation")
            print()

            choice = input("Enter 1, 2, or 3 [default 1]: ").strip()

            if choice == "2":
                extension_id = input("Enter your Chrome Extension ID: ").strip()
            elif choice == "3":
                chrome_browsers = []
                print("Skipping Chrome-based browsers.")
            else:
                # Default compiled extension ID
                extension_id = "kiepegiehgkjkbebfagoadghjdfkegpc"

        if chrome_browsers:
            print()
            print(f"Using Extension ID: {extension_id}")
            print()

            # Create Chrome manifest
            chrome_manifest = build_chrome_manifest(extension_id)
            manifest_path = script_dir / "native_manifest_chrome.json"
            create_manifest_file(chrome_manifest, manifest_path)

            # Register for each browser
            for browser in chrome_browsers:
                if browser == "Chrome":
                    if register_chrome_manifest(manifest_path):
                        results.append(f"[OK] Registered for Google Chrome")
                    else:
                        results.append(f"[FAIL] Failed to register for Google Chrome")

                elif browser == "Edge":
                    if register_edge_manifest(manifest_path):
                        results.append(f"[OK] Registered for Microsoft Edge")
                    else:
                        results.append(f"[FAIL] Failed to register for Microsoft Edge")

                elif browser == "Brave":
                    if register_brave_manifest(manifest_path):
                        results.append(f"[OK] Registered for Brave Browser")
                    else:
                        results.append(f"[FAIL] Failed to register for Brave Browser")

    # Check for Firefox
    if check_browser_installed("Firefox"):
        print("[+] Detected Mozilla Firefox")
        print()

        # Create Firefox manifest
        firefox_manifest = build_firefox_manifest()
        manifest_path = script_dir / "native_manifest_firefox.json"
        create_manifest_file(firefox_manifest, manifest_path)

        # Register for Firefox
        if register_firefox_manifest(manifest_path):
            results.append(f"[OK] Registered for Mozilla Firefox")
        else:
            results.append(f"[FAIL] Failed to register for Mozilla Firefox")

    # Print results
    print()
    print("=" * 60)
    print("Installation Results:")
    print("=" * 60)
    for result in results:
        print(result)

    if not results:
        print("[!] No supported browsers detected!")
        print()
        print("Supported browsers: Chrome, Edge, Firefox, Brave")

    print()
    print("=" * 60)

    return len([r for r in results if r.startswith("[OK]")]) > 0

if __name__ == "__main__":
    import argparse

    # Check if running on Windows
    if sys.platform != "win32":
        print("This script is for Windows only!")
        print("On Linux/macOS, use: bash install/browsers.sh")
        sys.exit(1)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install browser native messaging host for Windows")
    parser.add_argument("--silent", action="store_true", help="Run in silent mode (no prompts)")
    parser.add_argument("--extension-id", type=str, help="Chrome extension ID (default: compiled extension)")
    args = parser.parse_args()

    try:
        # If silent mode, use default extension ID
        if args.silent:
            extension_id = args.extension_id or "kiepegiehgkjkbebfagoadghjdfkegpc"
            success = install_browsers_manifest(extension_id=extension_id)
        else:
            success = install_browsers_manifest(extension_id=args.extension_id)

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
