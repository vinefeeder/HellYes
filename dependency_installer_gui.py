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
        self.root.geometry("900x700")

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
        """Show interactive device.wvd installation wizard"""
        window = Toplevel(self.root)
        window.title("Widevine Device Installation Wizard")
        window.geometry("750x600")
        window.transient(self.root)
        window.grab_set()
        window.lift()
        window.focus_force()

        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill=BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="📖 Widevine Device (device.wvd)", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        # Instructions
        inst_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        inst_frame.pack(fill=X, pady=(0, 10))

        inst_text = ttk.Label(inst_frame, text=(
            "You need client_id.bin and private_key.pem to create device.wvd.\n"
            "Use one of the options below:"
        ), font=("Arial", 9))
        inst_text.pack()

        # Status display
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=X, pady=(0, 10))

        status_label = ttk.Label(status_frame, text="Status: Waiting for files...", font=("Arial", 10))
        status_label.pack()

        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        log_text = scrolledtext.ScrolledText(log_frame, wrap=WORD, font=("Courier New", 9), height=10)
        log_text.pack(fill=BOTH, expand=True)

        def log_message(msg):
            log_text.insert(END, msg + "\n")
            log_text.see(END)
            log_text.update()

        def check_files():
            """Check if required files exist"""
            client_id = Path("client_id.bin").exists()
            private_key = Path("private_key.pem").exists()
            return client_id, private_key

        def update_status():
            """Update status based on file presence"""
            client_id, private_key = check_files()
            if client_id and private_key:
                status_label.config(text="✅ Both files found! Ready to create device.wvd", foreground="green")
                create_btn.config(state=NORMAL)
                return True
            elif client_id:
                status_label.config(text="⚠️ Found client_id.bin, missing private_key.pem", foreground="orange")
                create_btn.config(state=DISABLED)
            elif private_key:
                status_label.config(text="⚠️ Found private_key.pem, missing client_id.bin", foreground="orange")
                create_btn.config(state=DISABLED)
            else:
                status_label.config(text="❌ Missing both files", foreground="red")
                create_btn.config(state=DISABLED)
            return False

        def create_device_wvd():
            """Create device.wvd from the files"""
            log_message("=" * 60)
            log_message("Creating device.wvd...")

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
                        wvd_file.rename("device.wvd")
                        log_message(f"✅ Renamed {wvd_file} to device.wvd")
                        log_message("✅ device.wvd created successfully!")
                        status_label.config(text="✅ device.wvd created successfully!", foreground="green")

                        messagebox.showinfo(
                            "Success",
                            "device.wvd has been created successfully!\n\nClose this window and click Re-check."
                        )
                    else:
                        log_message("❌ No .wvd file was created")
                        status_label.config(text="❌ Creation failed", foreground="red")
                else:
                    log_message(f"❌ Command failed with exit code {result.returncode}")
                    status_label.config(text="❌ Creation failed", foreground="red")

            except Exception as e:
                log_message(f"❌ Error: {str(e)}")
                status_label.config(text="❌ Creation failed", foreground="red")
                messagebox.showerror("Error", f"Failed to create device.wvd:\n{str(e)}")

            log_message("=" * 60)

        def download_from_url():
            """Download and extract ZIP from URL"""
            url = url_entry.get().strip()
            if not url:
                messagebox.showwarning("No URL", "Please enter a ZIP file URL")
                return

            log_message("=" * 60)
            log_message(f"Downloading from: {url}")

            try:
                import tempfile
                import zipfile
                import urllib.request

                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                    tmp_path = tmp_file.name

                log_message("Downloading...")
                urllib.request.urlretrieve(url, tmp_path)
                log_message("✅ Downloaded successfully")

                log_message("Extracting...")
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    zip_ref.extractall(".")
                log_message("✅ Extracted successfully")

                Path(tmp_path).unlink()
                log_message("=" * 60)

                # Check if files are now present
                if update_status():
                    messagebox.showinfo(
                        "Success",
                        "Files downloaded and extracted!\n\nNow click 'Create device.wvd' button."
                    )
                else:
                    messagebox.showwarning(
                        "Files Not Found",
                        "ZIP extracted but client_id.bin and/or private_key.pem not found in root of ZIP.\n\n"
                        "Please check the extracted files."
                    )

            except Exception as e:
                log_message(f"❌ Error: {str(e)}")
                messagebox.showerror("Error", f"Failed to download/extract:\n{str(e)}")

        def browse_files():
            """Open file browser to select files"""
            from tkinter import filedialog

            files = filedialog.askopenfilenames(
                title="Select client_id.bin and private_key.pem",
                filetypes=[("BIN/PEM files", "*.bin *.pem"), ("All files", "*.*")]
            )

            if files:
                log_message("=" * 60)
                log_message("Copying selected files...")
                for file_path in files:
                    src = Path(file_path)
                    dst = Path(".") / src.name
                    import shutil
                    shutil.copy2(src, dst)
                    log_message(f"✅ Copied {src.name}")
                log_message("=" * 60)
                update_status()

        # Option 1: Open forum link
        opt1_frame = ttk.LabelFrame(main_frame, text="Option 1: Get Files from Forum", padding="10")
        opt1_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(opt1_frame, text="Visit the forum to download CDM files:").pack(anchor=W)

        forum_btn_frame = ttk.Frame(opt1_frame)
        forum_btn_frame.pack(fill=X, pady=(5, 0))

        ttk.Button(forum_btn_frame, text="🌐 Open Forum Link",
                   command=lambda: [
                       webbrowser.open("https://forum.videohelp.com/threads/413719-Ready-to-use-CDMs-available-here"),
                       log_message("Opened forum link in browser")
                   ]).pack(side=LEFT, padx=(0, 5))

        ttk.Button(forum_btn_frame, text="📁 Browse for Files",
                   command=browse_files).pack(side=LEFT, padx=(0, 5))

        ttk.Button(forum_btn_frame, text="🔄 Check Files",
                   command=lambda: [update_status(), log_message("Checked for files")]).pack(side=LEFT)

        # Option 2: Download from URL
        opt2_frame = ttk.LabelFrame(main_frame, text="Option 2: Download from URL", padding="10")
        opt2_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(opt2_frame, text="Enter direct ZIP file URL:").pack(anchor=W)

        url_frame = ttk.Frame(opt2_frame)
        url_frame.pack(fill=X, pady=(5, 0))

        url_entry = ttk.Entry(url_frame, width=50)
        url_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        ttk.Button(url_frame, text="📥 Download & Extract",
                   command=download_from_url).pack(side=LEFT)

        # Create button
        create_frame = ttk.Frame(main_frame)
        create_frame.pack(fill=X, pady=(10, 0))

        create_btn = ttk.Button(create_frame, text="🎯 Create device.wvd",
                                command=create_device_wvd, state=DISABLED)
        create_btn.pack(side=LEFT, padx=(0, 5))

        ttk.Button(create_frame, text="Close", command=window.destroy).pack(side=RIGHT)

        # Initial status check
        update_status()
        log_message("Wizard started. Choose an option above to get the required files.")

    def show_n_m3u8dl_re_instructions(self):
        """Show instructions for N_m3u8DL-RE"""
        window = Toplevel(self.root)
        window.title("Manual Installation: N_m3u8DL-RE")
        window.geometry("700x450")

        frame = ttk.Frame(window, padding="20")
        frame.pack(fill=BOTH, expand=True)

        title = ttk.Label(frame, text="📖 N_m3u8DL-RE", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))

        text = scrolledtext.ScrolledText(frame, wrap=WORD, font=("Arial", 10), height=15)
        text.pack(fill=BOTH, expand=True)

        instructions = """N_m3u8DL-RE is a command-line tool for downloading HLS/DASH streams.

Installation Steps:
  1. Visit: https://github.com/nilaoda/N_m3u8DL-RE/releases
  2. Download the appropriate binary for your platform:
     - Linux: N_m3u8DL-RE_Beta_linux-x64
     - Windows: N_m3u8DL-RE_Beta_win-x64.exe
     - macOS: N_m3u8DL-RE_Beta_osx-x64
  3. Extract the executable
  4. Rename it to: N_m3u8DL-RE (without extension on Linux/macOS)
  5. Make it executable (Linux/macOS): chmod +x N_m3u8DL-RE
  6. Place it in: ./bin/N_m3u8DL-RE
     OR add it to your system PATH

After installation, close this window and click "Re-check" to verify."""

        text.insert("1.0", instructions)
        text.config(state=DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(btn_frame, text="Open GitHub Releases",
                   command=lambda: webbrowser.open("https://github.com/nilaoda/N_m3u8DL-RE/releases")).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=window.destroy).pack(side=LEFT, padx=5)

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
