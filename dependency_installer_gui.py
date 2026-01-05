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
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox

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
        # Check in bin/ first, then system PATH
        if Path("bin/N_m3u8DL-RE").exists():
            return True
        return DependencyInstaller.check_command('N_m3u8DL-RE')

    @staticmethod
    def check_ffmpeg():
        """Check if ffmpeg is available"""
        if Path("bin/ffmpeg").exists():
            return True
        return DependencyInstaller.check_command('ffmpeg')

    @staticmethod
    def check_mp4decrypt():
        """Check if mp4decrypt is available"""
        if Path("bin/mp4decrypt").exists():
            return True
        return DependencyInstaller.check_command('mp4decrypt')

    @staticmethod
    def check_mkvmerge():
        """Check if mkvmerge is available"""
        if Path("bin/mkvmerge").exists():
            return True
        return DependencyInstaller.check_command('mkvmerge')

    @staticmethod
    def check_browser_manifest():
        """Check if browser manifest is installed"""
        chrome_manifest = Path.home() / ".config/google-chrome/NativeMessagingHosts/org.hellyes.hellyes.json"
        firefox_manifest = Path.home() / ".mozilla/native-messaging-hosts/org.hellyes.hellyes.json"
        return chrome_manifest.exists() or firefox_manifest.exists()


class DependencyStep:
    """Represents a single installation step with UI elements"""

    def __init__(self, parent_frame, gui, name, description, check_func, install_func,
                 manual_instructions_func=None, auto_install=True):
        self.parent_frame = parent_frame
        self.gui = gui
        self.name = name
        self.description = description
        self.check_func = check_func
        self.install_func = install_func
        self.manual_instructions_func = manual_instructions_func
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
                command=self.recheck
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
        self.gui.update_progress()

        if self.check():
            self.mark_complete(True)
            self.log("✅ Dependency found!", show_log=False)
            messagebox.showinfo(
                "Success!",
                f"✅ {self.name} is now detected and ready to use!"
            )
        else:
            self.set_status("⚠️ Still Not Found", "orange")
            messagebox.showwarning(
                "Not Found",
                f"❌ {self.name} is still not detected.\n\nPlease follow the manual instructions and try again."
            )

        self.gui.update_progress()

    def show_manual_instructions(self):
        """Show manual installation instructions"""
        if self.manual_instructions_func:
            try:
                self.manual_instructions_func()
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to show manual instructions:\n{str(e)}"
                )
        else:
            messagebox.showinfo(
                "Manual Installation",
                f"Please install {self.name} manually.\n\nNo specific instructions available."
            )

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
        self.root.geometry("950x800")
        self.root.minsize(900, 700)  # Set minimum size to ensure all content is visible
        self.root.maxsize(1400, 900)  # Set max size for small screens

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

        # Create canvas and scrollbar
        canvas = Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=canvas.yview)

        # Create frame inside canvas
        self.steps_frame = ttk.Frame(canvas)

        # Configure scroll region
        self.steps_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Create window in canvas
        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw", width=850)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=X, side=BOTTOM)

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

        # Ensure bin directory exists
        Path("bin").mkdir(exist_ok=True)

        # Step 1: Python
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "Python 3 & pip",
            "Python 3 interpreter and pip package manager",
            installer.check_python,
            self.install_python,
            auto_install=True
        ))

        # Step 2: Virtual Environment
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "Python Virtual Environment",
            "Create venv and install Python dependencies from requirements.txt",
            installer.check_venv,
            self.install_venv,
            auto_install=True
        ))

        # Step 3: Device WVD
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "Widevine Device (device.wvd)",
            "Widevine L3 CDM device file for DRM content",
            installer.check_device_wvd,
            self.install_device_wvd,
            manual_instructions_func=self.show_device_wvd_instructions,
            auto_install=False
        ))

        # Step 4: N_m3u8DL-RE
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "N_m3u8DL-RE",
            "HLS/DASH downloader - https://github.com/nilaoda/N_m3u8DL-RE",
            installer.check_n_m3u8dl_re,
            self.install_n_m3u8dl_re,
            manual_instructions_func=self.show_n_m3u8dl_re_instructions,
            auto_install=False
        ))

        # Step 5: FFmpeg
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "FFmpeg",
            "Audio/video processing tool",
            installer.check_ffmpeg,
            self.install_ffmpeg,
            manual_instructions_func=self.show_ffmpeg_instructions,
            auto_install=True
        ))

        # Step 6: mp4decrypt (Bento4)
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "mp4decrypt (Bento4)",
            "MP4 decryption tool - https://www.bento4.com/downloads/",
            installer.check_mp4decrypt,
            self.install_mp4decrypt,
            manual_instructions_func=self.show_mp4decrypt_instructions,
            auto_install=False
        ))

        # Step 7: mkvmerge
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
            "mkvmerge (MKVToolNix)",
            "MKV file manipulation tool - https://mkvtoolnix.download/",
            installer.check_mkvmerge,
            self.install_mkvmerge,
            manual_instructions_func=self.show_mkvmerge_instructions,
            auto_install=False
        ))

        # Step 8: Browser Manifest
        self.steps.append(DependencyStep(
            self.steps_frame,
            self,
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
        self.progress_bar['value'] = (completed / total) * 100 if total > 0 else 0

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
        step.log("This step requires running the installation script...")
        step.log("Please run: bash install/browsers.sh")
        return False

    # Manual instruction dialogs

    def show_device_wvd_instructions(self):
        """Show interactive device.wvd installation wizard with auto-detection"""
        window = Toplevel(self.root)
        window.title("Widevine Device Installation Wizard")
        window.geometry("800x600")
        window.minsize(750, 550)  # Set minimum size
        window.maxsize(1200, 800)  # Set max size for small screens
        window.transient(self.root)
        window.grab_set()
        window.lift()
        window.focus_force()

        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="📖 Widevine Device (device.wvd)", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        # Instructions
        inst_frame = ttk.LabelFrame(main_frame, text="📋 Instructions", padding="10")
        inst_frame.pack(fill=X, pady=(0, 10))

        working_dir = Path.cwd()
        inst_text = ttk.Label(inst_frame, text=(
            f"Place these files in the root directory:\n"
            f"  • client_id.bin\n"
            f"  • private_key.pem\n\n"
            f"Root directory: {working_dir}\n\n"
            f"The wizard will automatically detect the files and create device.wvd for you."
        ), font=("Arial", 9), justify=LEFT)
        inst_text.pack(anchor=W)

        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=X, pady=(0, 10))

        status_label = ttk.Label(status_frame, text="🔍 Checking for files...", font=("Arial", 11, "bold"))
        status_label.pack()

        # File status indicators
        file_status_frame = ttk.Frame(main_frame)
        file_status_frame.pack(fill=X, pady=(0, 10))

        client_id_label = ttk.Label(file_status_frame, text="❌ client_id.bin: Not found", font=("Arial", 9))
        client_id_label.pack(anchor=W, padx=20)

        private_key_label = ttk.Label(file_status_frame, text="❌ private_key.pem: Not found", font=("Arial", 9))
        private_key_label.pack(anchor=W, padx=20)

        # Buttons frame (pack BEFORE log area so it's always visible)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(10, 0))

        # Log area (now packs AFTER buttons are positioned at bottom)
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        log_text = scrolledtext.ScrolledText(log_frame, wrap=WORD, font=("Courier New", 9), height=12)
        log_text.pack(fill=BOTH, expand=True)

        def log_message(msg):
            log_text.insert(END, msg + "\n")
            log_text.see(END)
            log_text.update()

        def check_and_create():
            """Check for files and automatically create device.wvd"""
            log_message("Checking for required files...")

            client_id_exists = Path("client_id.bin").exists()
            private_key_exists = Path("private_key.pem").exists()

            # Update file status indicators
            if client_id_exists:
                client_id_label.config(text="✅ client_id.bin: Found", foreground="green")
                log_message("✅ Found client_id.bin")
            else:
                client_id_label.config(text="❌ client_id.bin: Not found", foreground="red")
                log_message("❌ Missing client_id.bin")

            if private_key_exists:
                private_key_label.config(text="✅ private_key.pem: Found", foreground="green")
                log_message("✅ Found private_key.pem")
            else:
                private_key_label.config(text="❌ private_key.pem: Not found", foreground="red")
                log_message("❌ Missing private_key.pem")

            # If both files exist, automatically create device.wvd
            if client_id_exists and private_key_exists:
                status_label.config(text="✅ Both files found! Creating device.wvd...", foreground="green")
                log_message("=" * 60)
                log_message("📦 Creating device.wvd automatically...")

                try:
                    # Run pywidevine command
                    cmd = ['./venv/bin/pywidevine', 'create-device', '-k', 'private_key.pem',
                           '-c', 'client_id.bin', '-t', 'ANDROID', '-l', '3']

                    log_message(f"Running: {' '.join(cmd)}")

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    log_message(result.stdout)
                    if result.stderr:
                        log_message(result.stderr)

                    if result.returncode == 0:
                        # Find and rename the .wvd file
                        wvd_files = list(Path(".").glob("*.wvd"))
                        if wvd_files:
                            wvd_file = wvd_files[0]
                            if wvd_file.name != "device.wvd":
                                wvd_file.rename("device.wvd")
                                log_message(f"✅ Renamed {wvd_file.name} to device.wvd")
                            log_message("=" * 60)
                            log_message("🎉 device.wvd created successfully!")
                            status_label.config(text="🎉 Success! device.wvd created", foreground="green")

                            # Update the main installer step
                            for step in self.steps:
                                if step.name == "Widevine Device (device.wvd)":
                                    step.mark_complete(True)
                                    break

                            self.update_progress()

                            messagebox.showinfo(
                                "Success!",
                                "✅ device.wvd has been created successfully!\n\n"
                                "The wizard will now close."
                            )
                            window.destroy()
                            return
                        else:
                            log_message("❌ No .wvd file was created")
                            status_label.config(text="❌ Creation failed - no .wvd file generated", foreground="red")
                    else:
                        log_message(f"❌ Command failed with exit code {result.returncode}")
                        status_label.config(text="❌ Creation failed - check log for details", foreground="red")

                except Exception as e:
                    log_message(f"❌ Error: {str(e)}")
                    status_label.config(text="❌ Creation failed - check log for details", foreground="red")

                log_message("=" * 60)
            else:
                status_label.config(text="⏳ Waiting for files to be placed in root directory", foreground="orange")
                log_message("⏳ Waiting for both files...")

        # Add buttons to the button_frame (already packed at bottom)
        ttk.Button(button_frame, text="🌐 Open Forum to Download Files",
                   command=lambda: [
                       webbrowser.open("https://forum.videohelp.com/threads/413719-Ready-to-use-CDMs-available-here"),
                       log_message("Opened forum in browser - download and place files in root directory")
                   ]).pack(side=LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="🔄 Check for Files Now",
                   command=check_and_create).pack(side=LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="❌ Close",
                   command=window.destroy).pack(side=RIGHT)

        # Periodic auto-check
        auto_check_active = [True]  # Use list to avoid closure issues

        def periodic_check():
            """Periodically check for files every 3 seconds"""
            if auto_check_active[0] and window.winfo_exists():
                try:
                    # Only check if device.wvd doesn't exist yet (successful creation closes window)
                    if not Path("device.wvd").exists():
                        check_and_create()
                        window.after(3000, periodic_check)  # Check every 3 seconds
                except:
                    pass

        # Stop auto-check when window closes
        def on_close():
            auto_check_active[0] = False
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_close)

        # Initial check and start periodic checking
        log_message("Wizard started.")
        log_message(f"Root directory: {working_dir}")
        log_message("Auto-checking every 3 seconds for files...")
        log_message("-" * 60)
        window.after(500, check_and_create)  # Initial check after 500ms
        window.after(3500, periodic_check)   # Start periodic checking after 3.5s

    def show_n_m3u8dl_re_instructions(self):
        """Show interactive N_m3u8DL-RE installation wizard with auto-detection"""
        window = Toplevel(self.root)
        window.title("N_m3u8DL-RE Installation Wizard")
        window.geometry("800x550")
        window.minsize(750, 500)
        window.maxsize(1200, 800)
        window.transient(self.root)
        window.grab_set()
        window.lift()
        window.focus_force()

        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="📖 N_m3u8DL-RE", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        # Instructions
        inst_frame = ttk.LabelFrame(main_frame, text="📋 Instructions", padding="10")
        inst_frame.pack(fill=X, pady=(0, 10))

        bin_dir = Path("./bin").absolute()
        inst_text = ttk.Label(inst_frame, text=(
            f"Download N_m3u8DL-RE and place it in:\n"
            f"  📁 {bin_dir}/N_m3u8DL-RE\n\n"
            f"Platform-specific filenames:\n"
            f"  • Linux: N_m3u8DL-RE_Beta_linux-x64\n"
            f"  • Windows: N_m3u8DL-RE_Beta_win-x64.exe\n"
            f"  • macOS: N_m3u8DL-RE_Beta_osx-x64\n\n"
            f"The wizard will automatically detect when the file is placed."
        ), font=("Arial", 9), justify=LEFT)
        inst_text.pack(anchor=W)

        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=X, pady=(0, 10))

        status_label = ttk.Label(status_frame, text="🔍 Checking for N_m3u8DL-RE...", font=("Arial", 11, "bold"))
        status_label.pack()

        # File status indicator
        file_status_frame = ttk.Frame(main_frame)
        file_status_frame.pack(fill=X, pady=(0, 10))

        file_label = ttk.Label(file_status_frame, text="❌ N_m3u8DL-RE: Not found", font=("Arial", 9))
        file_label.pack(anchor=W, padx=20)

        # Buttons frame (pack at bottom first)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(10, 0))

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        log_text = scrolledtext.ScrolledText(log_frame, wrap=WORD, font=("Courier New", 9), height=10)
        log_text.pack(fill=BOTH, expand=True)

        def log_message(msg):
            log_text.insert(END, msg + "\n")
            log_text.see(END)
            log_text.update()

        def check_file():
            """Check if N_m3u8DL-RE exists"""
            log_message("Checking for N_m3u8DL-RE...")

            # Check in bin/ directory
            bin_path = Path("./bin/N_m3u8DL-RE")
            system_path = DependencyInstaller.check_command('N_m3u8DL-RE')

            if bin_path.exists():
                file_label.config(text=f"✅ N_m3u8DL-RE: Found in ./bin/", foreground="green")
                status_label.config(text="✅ N_m3u8DL-RE found!", foreground="green")
                log_message(f"✅ Found: {bin_path.absolute()}")

                # Check if executable
                if not bin_path.stat().st_mode & 0o111:
                    log_message("⚠️  File is not executable. Making it executable...")
                    bin_path.chmod(bin_path.stat().st_mode | 0o111)
                    log_message("✅ File is now executable")

                # Update the main installer step
                for step in self.steps:
                    if step.name == "N_m3u8DL-RE":
                        step.mark_complete(True)
                        break

                self.update_progress()

                messagebox.showinfo(
                    "Success!",
                    "✅ N_m3u8DL-RE has been found and configured!\n\n"
                    "The wizard will now close."
                )
                window.destroy()
                return True

            elif system_path:
                file_label.config(text="✅ N_m3u8DL-RE: Found in system PATH", foreground="green")
                status_label.config(text="✅ N_m3u8DL-RE found in system!", foreground="green")
                log_message("✅ Found in system PATH")

                # Update the main installer step
                for step in self.steps:
                    if step.name == "N_m3u8DL-RE":
                        step.mark_complete(True)
                        break

                self.update_progress()

                messagebox.showinfo(
                    "Success!",
                    "✅ N_m3u8DL-RE is installed in your system!\n\n"
                    "The wizard will now close."
                )
                window.destroy()
                return True

            else:
                file_label.config(text="❌ N_m3u8DL-RE: Not found", foreground="red")
                status_label.config(text="⏳ Waiting for file to be placed in ./bin/", foreground="orange")
                log_message(f"❌ Not found in: {bin_path.absolute()}")
                log_message("❌ Not found in system PATH")
                log_message("⏳ Waiting for file...")
                return False

        # Add buttons
        ttk.Button(button_frame, text="🌐 Open GitHub Releases Page",
                   command=lambda: [
                       webbrowser.open("https://github.com/nilaoda/N_m3u8DL-RE/releases"),
                       log_message("Opened GitHub releases in browser")
                   ]).pack(side=LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="🔄 Check for File Now",
                   command=check_file).pack(side=LEFT, padx=(0, 5))

        ttk.Button(button_frame, text="❌ Close",
                   command=window.destroy).pack(side=RIGHT)

        # Periodic auto-check
        auto_check_active = [True]

        def periodic_check():
            """Periodically check for file every 3 seconds"""
            if auto_check_active[0] and window.winfo_exists():
                try:
                    # Always call check_file, it will close window if found
                    result = check_file()
                    # Only continue periodic checking if file not found
                    if not result:
                        window.after(3000, periodic_check)
                except:
                    pass

        def on_close():
            auto_check_active[0] = False
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_close)

        # Initial check
        log_message("Wizard started.")
        log_message(f"Target directory: {bin_dir}")
        log_message("Auto-checking every 3 seconds for file...")
        log_message("-" * 60)
        window.after(500, check_file)
        window.after(3500, periodic_check)

    def show_ffmpeg_instructions(self):
        """Show instructions for FFmpeg"""
        window = Toplevel(self.root)
        window.title("Manual Installation: FFmpeg")
        window.geometry("700x450")

        frame = ttk.Frame(window, padding="20")
        frame.pack(fill=BOTH, expand=True)

        title = ttk.Label(frame, text="📖 FFmpeg", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        text = scrolledtext.ScrolledText(frame, wrap=WORD, font=("Arial", 10), height=15)
        text.pack(fill=BOTH, expand=True)

        instructions = """FFmpeg is a powerful multimedia framework.

Installation Options:

Option 1: Package Manager (Recommended)
  Ubuntu/Debian: sudo apt-get install ffmpeg
  Fedora: sudo dnf install ffmpeg
  Arch: sudo pacman -S ffmpeg
  macOS: brew install ffmpeg

Option 2: Manual Installation
  1. Visit: https://ffmpeg.org/download.html
  2. Download the appropriate build for your platform
  3. Extract the ffmpeg executable
  4. Place it in: ./bin/ffmpeg
     OR add it to your system PATH

After installation, close this window and click "Re-check" to verify."""

        text.insert("1.0", instructions)
        text.config(state=DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(btn_frame, text="Open FFmpeg Website",
                   command=lambda: webbrowser.open("https://ffmpeg.org/download.html")).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=window.destroy).pack(side=LEFT, padx=5)

    def show_mp4decrypt_instructions(self):
        """Show instructions for mp4decrypt"""
        window = Toplevel(self.root)
        window.title("Manual Installation: mp4decrypt")
        window.geometry("700x450")

        frame = ttk.Frame(window, padding="20")
        frame.pack(fill=BOTH, expand=True)

        title = ttk.Label(frame, text="📖 mp4decrypt (Bento4)", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        text = scrolledtext.ScrolledText(frame, wrap=WORD, font=("Arial", 10), height=15)
        text.pack(fill=BOTH, expand=True)

        instructions = """mp4decrypt is part of the Bento4 toolkit for MP4 files.

Installation Steps:
  1. Visit: https://www.bento4.com/downloads/
  2. Download Bento4 tools for your platform:
     - Linux: Bento4-SDK-*-x86_64-unknown-linux.zip
     - Windows: Bento4-SDK-*-x86_64-microsoft-win32.zip
     - macOS: Bento4-SDK-*-universal-apple-macosx.zip
  3. Extract the archive
  4. Locate the mp4decrypt executable in the bin/ folder
  5. Copy mp4decrypt to: ./bin/mp4decrypt
     OR add it to your system PATH

After installation, close this window and click "Re-check" to verify."""

        text.insert("1.0", instructions)
        text.config(state=DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(btn_frame, text="Open Bento4 Downloads",
                   command=lambda: webbrowser.open("https://www.bento4.com/downloads/")).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=window.destroy).pack(side=LEFT, padx=5)

    def show_mkvmerge_instructions(self):
        """Show instructions for mkvmerge"""
        window = Toplevel(self.root)
        window.title("Manual Installation: mkvmerge")
        window.geometry("700x450")

        frame = ttk.Frame(window, padding="20")
        frame.pack(fill=BOTH, expand=True)

        title = ttk.Label(frame, text="📖 mkvmerge (MKVToolNix)", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        text = scrolledtext.ScrolledText(frame, wrap=WORD, font=("Arial", 10), height=15)
        text.pack(fill=BOTH, expand=True)

        instructions = """mkvmerge is part of MKVToolNix for working with Matroska files.

Installation Options:

Option 1: Package Manager (Recommended)
  Ubuntu/Debian: sudo apt-get install mkvtoolnix
  Fedora: sudo dnf install mkvtoolnix
  Arch: sudo pacman -S mkvtoolnix-cli
  macOS: brew install mkvtoolnix

Option 2: Manual Installation
  1. Visit: https://mkvtoolnix.download/downloads.html
  2. Download MKVToolNix for your platform
  3. Install or extract mkvmerge executable
  4. Place it in: ./bin/mkvmerge
     OR add it to your system PATH

After installation, close this window and click "Re-check" to verify."""

        text.insert("1.0", instructions)
        text.config(state=DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(btn_frame, text="Open MKVToolNix Website",
                   command=lambda: webbrowser.open("https://mkvtoolnix.download/downloads.html")).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=window.destroy).pack(side=LEFT, padx=5)


def main():
    root = Tk()
    app = InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
