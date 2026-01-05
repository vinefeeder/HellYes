#!/usr/bin/env python3
"""
dependency_installer_gui.py - GUI installer for HellShared dependencies
Shows step-by-step progress with checkboxes for each dependency
"""

import sys
import os
import subprocess
import platform
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, filedialog

class DependencyInstaller:
    """Handles checking and installing individual dependencies"""

    @staticmethod
    def run_command(cmd, shell=False):
        """Run a command and return success status and output"""
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_command(cmd):
        """Check if a command is available"""
        try:
            result = subprocess.run(
                ['which', cmd] if platform.system() != 'Windows' else ['where', cmd],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def check_file(path):
        """Check if a file exists"""
        return Path(path).exists()

    @staticmethod
    def check_python():
        """Check if Python 3 and pip3 are available"""
        return DependencyInstaller.check_command('python3') and DependencyInstaller.check_command('pip3')

    @staticmethod
    def check_venv():
        """Check if venv exists and has dependencies installed"""
        venv_python = Path("venv/bin/python3")
        if platform.system() == 'Windows':
            venv_python = Path("venv/Scripts/python.exe")
        return venv_python.exists()

    @staticmethod
    def check_device_wvd():
        """Check if device.wvd exists"""
        return Path("device.wvd").exists()

    @staticmethod
    def check_n_m3u8dl_re():
        """Check if N_m3u8DL-RE is available"""
        return DependencyInstaller.check_command('N_m3u8DL-RE') or Path("bin/N_m3u8DL-RE").exists()

    @staticmethod
    def check_ffmpeg():
        """Check if ffmpeg is available"""
        return DependencyInstaller.check_command('ffmpeg') or Path("bin/ffmpeg").exists()

    @staticmethod
    def check_mp4decrypt():
        """Check if mp4decrypt is available"""
        return DependencyInstaller.check_command('mp4decrypt') or Path("bin/mp4decrypt").exists()

    @staticmethod
    def check_mkvmerge():
        """Check if mkvmerge is available"""
        return DependencyInstaller.check_command('mkvmerge') or Path("bin/mkvmerge").exists()

    @staticmethod
    def check_browser_manifest():
        """Check if browser manifest is installed"""
        chrome_manifest = Path.home() / ".config/google-chrome/NativeMessagingHosts/org.hellyes.hellyes.json"
        firefox_manifest = Path.home() / ".mozilla/native-messaging-hosts/org.hellyes.hellyes.json"
        return chrome_manifest.exists() or firefox_manifest.exists()


class DependencyStep:
    """Represents a single installation step with UI elements"""

    def __init__(self, parent_frame, name, description, check_func, install_func, auto_install=True):
        self.name = name
        self.description = description
        self.check_func = check_func
        self.install_func = install_func
        self.auto_install = auto_install
        self.is_complete = False

        # Create frame for this step
        self.frame = ttk.Frame(parent_frame, relief=RIDGE, borderwidth=2)
        self.frame.pack(fill=X, padx=10, pady=5)

        # Header frame with checkbox
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=X, padx=10, pady=5)

        self.checkbox_var = BooleanVar(value=False)
        self.checkbox = ttk.Checkbutton(header_frame, variable=self.checkbox_var, state=DISABLED)
        self.checkbox.pack(side=LEFT)

        self.name_label = ttk.Label(
            header_frame,
            text=name,
            font=("Arial", 11, "bold")
        )
        self.name_label.pack(side=LEFT, padx=5)

        self.status_label = ttk.Label(
            header_frame,
            text="⏳ Pending",
            font=("Arial", 10)
        )
        self.status_label.pack(side=RIGHT)

        # Description
        desc_label = ttk.Label(
            self.frame,
            text=description,
            font=("Arial", 9),
            foreground="gray"
        )
        desc_label.pack(fill=X, padx=30, pady=(0, 5))

        # Log text area (hidden by default)
        self.log_frame = ttk.Frame(self.frame)
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=WORD,
            font=("Courier New", 8),
            bg="#f5f5f5",
            height=6
        )
        self.log_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Manual install button (for non-auto steps)
        if not self.auto_install:
            btn_frame = ttk.Frame(self.frame)
            btn_frame.pack(fill=X, padx=30, pady=(0, 10))

            self.manual_button = ttk.Button(
                btn_frame,
                text="📖 Manual Instructions",
                command=self.show_manual_instructions
            )
            self.manual_button.pack(side=LEFT, padx=5)

            self.recheck_button = ttk.Button(
                btn_frame,
                text="🔄 Re-check",
                command=self.recheck,
                state=DISABLED
            )
            self.recheck_button.pack(side=LEFT, padx=5)

    def log(self, message, show_log=True):
        """Add message to this step's log"""
        if show_log and not self.log_frame.winfo_ismapped():
            self.log_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.update()

    def set_status(self, status, color="black"):
        """Update status label"""
        self.status_label.config(text=status, foreground=color)
        self.status_label.update()

    def mark_complete(self, success=True):
        """Mark step as complete"""
        self.is_complete = success
        self.checkbox_var.set(success)

        if success:
            self.set_status("✅ Complete", "green")
            self.name_label.config(foreground="green")
        else:
            self.set_status("⚠️ Needs Attention", "orange")
            self.name_label.config(foreground="orange")

            if not self.auto_install:
                self.recheck_button.config(state=NORMAL)

    def check(self):
        """Check if this dependency is installed"""
        try:
            return self.check_func()
        except Exception as e:
            self.log(f"Error checking: {str(e)}")
            return False

    def recheck(self):
        """Re-check the dependency (for manual steps)"""
        self.set_status("🔄 Checking...", "blue")
        if self.check():
            self.mark_complete(True)
        else:
            self.set_status("⚠️ Still Not Found", "orange")
            messagebox.showinfo(
                "Not Found",
                f"{self.name} is still not detected.\n\nPlease follow the manual instructions and try again."
            )

    def show_manual_instructions(self):
        """Show manual installation instructions"""
        # This will be overridden by specific implementations
        pass

    def install(self):
        """Install this dependency"""
        self.set_status("🔄 Installing...", "blue")
        self.log(f"Starting installation of {self.name}...")
        self.log("=" * 60)

        try:
            success = self.install_func(self)
            self.mark_complete(success)

            if success:
                self.log("=" * 60)
                self.log(f"✅ {self.name} installed successfully!")
            else:
                self.log("=" * 60)
                self.log(f"⚠️ {self.name} installation needs attention")

            return success
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.mark_complete(False)
            return False


class InstallerGUI:
    """Main installer GUI window"""

    def __init__(self, root):
        self.root = root
        self.root.title("HellShared Dependency Installer")
        self.root.geometry("900x800")

        self.steps = []
        self.current_step_index = 0
        self.is_installing = False

        self.setup_ui()
        self.setup_steps()
        self.check_all_dependencies()

    def setup_ui(self):
        """Setup the main UI"""
        # Title
        title_frame = ttk.Frame(self.root, padding="15")
        title_frame.pack(fill=X)

        title_label = ttk.Label(
            title_frame,
            text="HellShared Dependency Installer",
            font=("Arial", 18, "bold")
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            title_frame,
            text="Install all required dependencies for HellShared",
            font=("Arial", 10),
            foreground="gray"
        )
        subtitle_label.pack()

        # Progress bar
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill=X)

        self.progress_label = ttk.Label(
            progress_frame,
            text="Progress: 0/0 dependencies installed",
            font=("Arial", 10, "bold")
        )
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=5)

        # Scrollable frame for steps
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        canvas = Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=canvas.yview)

        self.steps_frame = ttk.Frame(canvas)
        self.steps_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=X)

        self.install_button = ttk.Button(
            button_frame,
            text="🚀 Install All Dependencies",
            command=self.start_installation
        )
        self.install_button.pack(side=LEFT, padx=5)

        self.check_button = ttk.Button(
            button_frame,
            text="🔄 Re-check All",
            command=self.check_all_dependencies
        )
        self.check_button.pack(side=LEFT, padx=5)

        self.close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.root.quit
        )
        self.close_button.pack(side=RIGHT, padx=5)

    def setup_steps(self):
        """Setup all installation steps"""
        installer = DependencyInstaller()

        # Step 1: Python
        self.steps.append(DependencyStep(
            self.steps_frame,
            "Python 3 & pip",
            "Python 3 interpreter and pip package manager",
            installer.check_python,
            self.install_python,
            auto_install=True
        ))

        # Step 2: Virtual Environment
        self.steps.append(DependencyStep(
            self.steps_frame,
            "Python Virtual Environment",
            "Create venv and install Python dependencies from requirements.txt",
            installer.check_venv,
            self.install_venv,
            auto_install=True
        ))

        # Step 3: Device WVD
        self.steps.append(DependencyStep(
            self.steps_frame,
            "Widevine Device (device.wvd)",
            "Widevine L3 CDM device file for DRM content",
            installer.check_device_wvd,
            self.install_device_wvd,
            auto_install=False
        ))
        self.steps[-1].show_manual_instructions = lambda: self.show_device_wvd_instructions()

        # Step 4: N_m3u8DL-RE
        self.steps.append(DependencyStep(
            self.steps_frame,
            "N_m3u8DL-RE",
            "HLS/DASH downloader - https://github.com/nilaoda/N_m3u8DL-RE",
            installer.check_n_m3u8dl_re,
            self.install_n_m3u8dl_re,
            auto_install=False
        ))
        self.steps[-1].show_manual_instructions = lambda: self.show_n_m3u8dl_re_instructions()

        # Step 5: FFmpeg
        self.steps.append(DependencyStep(
            self.steps_frame,
            "FFmpeg",
            "Audio/video processing tool",
            installer.check_ffmpeg,
            self.install_ffmpeg,
            auto_install=True
        ))

        # Step 6: mp4decrypt (Bento4)
        self.steps.append(DependencyStep(
            self.steps_frame,
            "mp4decrypt (Bento4)",
            "MP4 decryption tool - https://www.bento4.com/downloads/",
            installer.check_mp4decrypt,
            self.install_mp4decrypt,
            auto_install=False
        ))
        self.steps[-1].show_manual_instructions = lambda: self.show_mp4decrypt_instructions()

        # Step 7: mkvmerge
        self.steps.append(DependencyStep(
            self.steps_frame,
            "mkvmerge (MKVToolNix)",
            "MKV file manipulation tool - https://mkvtoolnix.download/",
            installer.check_mkvmerge,
            self.install_mkvmerge,
            auto_install=False
        ))
        self.steps[-1].show_manual_instructions = lambda: self.show_mkvmerge_instructions()

        # Step 8: Browser Manifest
        self.steps.append(DependencyStep(
            self.steps_frame,
            "Browser Extension Manifest",
            "Native messaging host for browser extension",
            installer.check_browser_manifest,
            self.install_browser_manifest,
            auto_install=True
        ))

    def update_progress(self):
        """Update progress bar and label"""
        completed = sum(1 for step in self.steps if step.is_complete)
        total = len(self.steps)

        self.progress_label.config(text=f"Progress: {completed}/{total} dependencies installed")
        self.progress_bar['value'] = (completed / total) * 100

        # Update window
        self.root.update()

    def check_all_dependencies(self):
        """Check all dependencies and update UI"""
        for step in self.steps:
            if step.check():
                step.mark_complete(True)
            else:
                step.mark_complete(False)

        self.update_progress()

    def start_installation(self):
        """Start the installation process"""
        if self.is_installing:
            return

        # Ask for confirmation
        if not messagebox.askyesno(
            "Start Installation",
            "This will install all missing dependencies.\n\n"
            "Some steps may require manual intervention.\n\n"
            "Continue?"
        ):
            return

        self.is_installing = True
        self.install_button.config(state=DISABLED)
        self.check_button.config(state=DISABLED)

        # Start installation in background thread
        threading.Thread(target=self._install_all, daemon=True).start()

    def _install_all(self):
        """Install all dependencies"""
        for i, step in enumerate(self.steps):
            if step.is_complete:
                continue

            self.current_step_index = i

            # Check first
            if step.check():
                step.mark_complete(True)
                self.update_progress()
                continue

            # Install if auto-install is enabled
            if step.auto_install:
                step.install()
            else:
                step.mark_complete(False)

            self.update_progress()

        self.is_installing = False
        self.install_button.config(state=NORMAL)
        self.check_button.config(state=NORMAL)

        # Check if all complete
        all_complete = all(step.is_complete for step in self.steps)

        if all_complete:
            messagebox.showinfo(
                "Installation Complete",
                "✅ All dependencies are installed!\n\nYou can now use HellShared."
            )
        else:
            messagebox.showwarning(
                "Installation Incomplete",
                "Some dependencies need manual installation.\n\n"
                "Please follow the manual instructions for the incomplete steps."
            )

    # Installation functions for each step

    def install_python(self, step):
        """Install Python (auto-detect package manager)"""
        # Detect package manager
        pkg_managers = {
            'apt-get': 'sudo apt-get update && sudo apt-get install -y python3 python3-pip',
            'dnf': 'sudo dnf install -y python3 python3-pip',
            'yum': 'sudo yum install -y python3 python3-pip',
            'pacman': 'sudo pacman -S --noconfirm python python-pip',
            'brew': 'brew install python3'
        }

        for pm, cmd in pkg_managers.items():
            if DependencyInstaller.check_command(pm):
                step.log(f"Detected package manager: {pm}")
                step.log(f"Running: {cmd}")
                success, output = DependencyInstaller.run_command(cmd, shell=True)
                step.log(output)
                return success

        step.log("No supported package manager found.")
        step.log("Please install Python 3 and pip3 manually.")
        return False

    def install_venv(self, step):
        """Create virtual environment and install dependencies"""
        step.log("Creating virtual environment...")
        success, output = DependencyInstaller.run_command(['python3', '-m', 'venv', 'venv'])
        step.log(output)

        if not success:
            return False

        step.log("\nInstalling Python dependencies from requirements.txt...")

        pip_cmd = 'venv/bin/pip' if platform.system() != 'Windows' else 'venv\\Scripts\\pip.exe'
        success, output = DependencyInstaller.run_command([pip_cmd, 'install', '-r', 'requirements.txt'])
        step.log(output)

        return success

    def install_device_wvd(self, step):
        """Device WVD installation (manual)"""
        step.log("This requires manual installation.")
        step.log("Please follow the instructions by clicking 'Manual Instructions' button.")
        return False

    def install_n_m3u8dl_re(self, step):
        """N_m3u8DL-RE installation (manual)"""
        step.log("This requires manual download.")
        step.log("Please follow the instructions by clicking 'Manual Instructions' button.")
        return False

    def install_ffmpeg(self, step):
        """Install FFmpeg"""
        # Try package manager first
        pkg_managers = {
            'apt-get': 'sudo apt-get update && sudo apt-get install -y ffmpeg',
            'dnf': 'sudo dnf install -y ffmpeg',
            'yum': 'sudo yum install -y ffmpeg',
            'pacman': 'sudo pacman -S --noconfirm ffmpeg',
            'brew': 'brew install ffmpeg'
        }

        for pm, cmd in pkg_managers.items():
            if DependencyInstaller.check_command(pm):
                step.log(f"Detected package manager: {pm}")
                step.log(f"Running: {cmd}")
                success, output = DependencyInstaller.run_command(cmd, shell=True)
                step.log(output)
                return success

        step.log("No supported package manager found.")
        step.log("Please install FFmpeg manually from https://ffmpeg.org/download.html")
        return False

    def install_mp4decrypt(self, step):
        """mp4decrypt installation (manual)"""
        step.log("This requires manual download.")
        step.log("Please follow the instructions by clicking 'Manual Instructions' button.")
        return False

    def install_mkvmerge(self, step):
        """mkvmerge installation (manual)"""
        step.log("This requires manual download.")
        step.log("Please follow the instructions by clicking 'Manual Instructions' button.")
        return False

    def install_browser_manifest(self, step):
        """Install browser extension manifest"""
        step.log("Installing browser extension manifest...")

        # Run the browser installation script
        success, output = DependencyInstaller.run_command(['bash', 'install.sh'], shell=False)
        step.log(output)

        return success

    # Manual instruction dialogs

    def show_device_wvd_instructions(self):
        """Show instructions for device.wvd"""
        msg = """
📖 Manual Installation: Widevine Device (device.wvd)

You need to obtain a Widevine L3 CDM device file.

Option 1: Use existing client_id.bin and private_key.pem
  1. Place both files in the HellShared directory
  2. Run: ./venv/bin/pywidevine create-device -k private_key.pem -c client_id.bin -t "ANDROID" -l 3
  3. Rename the created .wvd file to device.wvd

Option 2: Download from repository
  1. Visit: https://forum.videohelp.com/threads/413719-Ready-to-use-CDMs-available-here
  2. Download a CDM package
  3. Extract client_id.bin and private_key.pem
  4. Follow Option 1 steps

After completing the steps, click "Re-check" to verify.
        """
        messagebox.showinfo("Manual Installation: device.wvd", msg)

    def show_n_m3u8dl_re_instructions(self):
        """Show instructions for N_m3u8DL-RE"""
        msg = """
📖 Manual Installation: N_m3u8DL-RE

1. Visit: https://github.com/nilaoda/N_m3u8DL-RE/releases
2. Download the appropriate binary for your platform
3. Extract the executable
4. Either:
   - Place it in the ./bin directory, OR
   - Place it in a directory in your PATH

After installing, click "Re-check" to verify.
        """
        messagebox.showinfo("Manual Installation: N_m3u8DL-RE", msg)

    def show_mp4decrypt_instructions(self):
        """Show instructions for mp4decrypt"""
        msg = """
📖 Manual Installation: mp4decrypt (Bento4)

1. Visit: https://www.bento4.com/downloads/
2. Download Bento4 tools for your platform
3. Extract mp4decrypt executable
4. Either:
   - Place it in the ./bin directory, OR
   - Place it in a directory in your PATH

After installing, click "Re-check" to verify.
        """
        messagebox.showinfo("Manual Installation: mp4decrypt", msg)

    def show_mkvmerge_instructions(self):
        """Show instructions for mkvmerge"""
        msg = """
📖 Manual Installation: mkvmerge (MKVToolNix)

1. Visit: https://mkvtoolnix.download/downloads.html
2. Download MKVToolNix for your platform
3. Install or extract mkvmerge executable
4. Either:
   - Place it in the ./bin directory, OR
   - Place it in a directory in your PATH

After installing, click "Re-check" to verify.
        """
        messagebox.showinfo("Manual Installation: mkvmerge", msg)


def main():
    root = Tk()
    app = InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
