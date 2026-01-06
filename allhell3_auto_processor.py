#!/usr/bin/env python3
"""
allhell3_auto_processor.py - Automatic JSON file processor with GUI
Monitors pending/ directory and automatically processes JSON files with allhell3.py
Supports parallel processing with tabbed interface
"""

import sys
import os
import time
import threading
import json
import platform
import re
import subprocess
from pathlib import Path

# Import pexpect based on platform
if platform.system() == 'Windows':
    import shlex
else:
    import pexpect
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

# Configuration
PENDING_DIR = Path("./pending")

# Ensure directories exist
PENDING_DIR.mkdir(exist_ok=True)


class ProcessingTab:
    """Represents a single processing job in a tab"""
    def __init__(self, notebook, filename, file_path, venv_python, parent_gui):
        self.notebook = notebook
        self.filename = filename
        self.file_path = file_path
        self.venv_python = venv_python
        self.parent_gui = parent_gui
        self.is_complete = False
        self.thread = None

        # Create tab frame
        self.tab_frame = ttk.Frame(notebook)
        notebook.add(self.tab_frame, text=f"⏳ {filename[:30]}...")

        # Create close button frame
        close_frame = ttk.Frame(self.tab_frame)
        close_frame.pack(fill=X, padx=5, pady=5)

        self.close_button = ttk.Button(
            close_frame,
            text="Close Tab",
            command=self.close_tab,
            state=DISABLED  # Disabled until process completes
        )
        self.close_button.pack(side=RIGHT)

        self.status_label = ttk.Label(
            close_frame,
            text=f"Processing: {filename}",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(side=LEFT)

        # Log area
        log_frame = ttk.Frame(self.tab_frame)
        log_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=WORD,
            font=("Courier New", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=BOTH, expand=True)

    def log(self, message):
        """Add message to this tab's log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        self.log_text.insert(END, log_line)
        self.log_text.see(END)
        self.log_text.update()

    def get_tab_index(self):
        """Get the current index of this tab by matching the tab_frame widget"""
        try:
            for i in range(self.notebook.index("end")):
                if self.notebook.nametowidget(self.notebook.tabs()[i]) == self.tab_frame:
                    return i
        except:
            pass
        return None

    def close_tab(self):
        """Close this tab"""
        try:
            tab_index = self.get_tab_index()
            if tab_index is not None:
                self.notebook.forget(tab_index)
                # Remove from parent's active tabs list
                if self in self.parent_gui.active_tabs:
                    self.parent_gui.active_tabs.remove(self)
        except Exception as e:
            print(f"Error closing tab: {e}")

    def mark_complete(self, success):
        """Mark the processing as complete"""
        self.is_complete = True
        self.close_button.config(state=NORMAL)

        try:
            # Get the tab index using the widget-based method
            tab_index = self.get_tab_index()

            if tab_index is not None:
                if success:
                    self.notebook.tab(tab_index, text=f"✓ {self.filename[:30]}...")
                    self.status_label.config(text=f"✓ Complete: {self.filename}", foreground="green")
                else:
                    self.notebook.tab(tab_index, text=f"✗ {self.filename[:30]}...")
                    self.status_label.config(text=f"✗ Failed: {self.filename}", foreground="red")
            else:
                # Fallback - just update status label if we can't find the tab
                if success:
                    self.status_label.config(text=f"✓ Complete: {self.filename}", foreground="green")
                else:
                    self.status_label.config(text=f"✗ Failed: {self.filename}", foreground="red")
        except Exception as e:
            print(f"Error marking complete: {e}")
            # Fallback - just update status label
            if success:
                self.status_label.config(text=f"✓ Complete: {self.filename}", foreground="green")
            else:
                self.status_label.config(text=f"✗ Failed: {self.filename}", foreground="red")

    def start_processing(self):
        """Start the processing in a background thread"""
        self.thread = threading.Thread(target=self._process, daemon=True)
        self.thread.start()

    def _process(self):
        """Process the file (runs in background thread)"""
        self.log(f"Starting processing: {self.filename}")
        self.log("=" * 60)

        try:
            if platform.system() == 'Windows':
                # Windows: Use subprocess directly with auto-confirmation
                self._process_windows()
            else:
                # Unix: Use pexpect for interactive control
                self._process_unix()

        except Exception as e:
            self.log(f"✗ Error processing {self.filename}: {str(e)}")
            self.mark_complete(False)

    def _process_windows(self):
        """Windows-specific processing using subprocess"""
        cmd = [self.venv_python, 'allhell3.py', self.file_path]

        # Create environment with UTF-8 encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        # Create process with pipes
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
            encoding='utf-8',
            errors='replace'
        )

        # Send Enter immediately to auto-confirm
        try:
            proc.stdin.write('\n')
            proc.stdin.flush()
        except:
            pass

        output_buffer = ""
        last_progress_lines = {}

        # Read output line by line
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break

            # Remove ANSI escape codes
            clean_line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', line)
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
            clean_line = clean_line.strip()

            if not clean_line:
                continue

            # Check if this is a progress bar line
            is_progress = '━' in clean_line or '%' in clean_line

            if is_progress:
                stream_id = None
                if clean_line.startswith('Vid'):
                    stream_id = 'Vid'
                elif clean_line.startswith('Aud'):
                    stream_id = 'Aud'

                if stream_id:
                    should_log = True
                    if stream_id in last_progress_lines:
                        last_line = last_progress_lines[stream_id]
                        try:
                            current_pct = float(re.search(r'(\d+\.\d+)%', clean_line).group(1))
                            last_pct = float(re.search(r'(\d+\.\d+)%', last_line).group(1))
                            if abs(current_pct - last_pct) < 5.0:
                                should_log = False
                        except:
                            pass

                    if should_log:
                        last_progress_lines[stream_id] = clean_line
                        self.log(clean_line)
            else:
                self.log(clean_line)

            # Auto-send Enter if prompt detected
            if "Enter to run" in line or "Ctrl‑C to abort" in line:
                self.log("[Auto-confirming - sending Enter...]")
                try:
                    proc.stdin.write('\n')
                    proc.stdin.flush()
                except:
                    pass

        # Wait for process to finish
        exit_code = proc.wait()

        self.log("=" * 60)

        if exit_code == 0:
            self.log(f"✓ Success: {self.filename}")

            # Delete the JSON file if deleteMe is True
            try:
                if os.path.exists(self.file_path):
                    with open(self.file_path, 'r') as f:
                        cfg = json.load(f)
                        if cfg.get('deleteMe', False):
                            os.remove(self.file_path)
                            self.log(f"Deleted: {self.filename}")
            except Exception as e:
                self.log(f"Note: Could not check/delete file: {str(e)}")

            self.mark_complete(True)
        else:
            self.log(f"✗ Failed: {self.filename} (exit code: {exit_code})")
            self.mark_complete(False)

    def _process_unix(self):
        """Unix-specific processing using pexpect"""
        cmd = f"{self.venv_python} allhell3.py '{self.file_path}'"
        child = pexpect.spawn(cmd, timeout=30, encoding='utf-8', cwd=os.getcwd())
        child.setwinsize(24, 120)

        output_buffer = ""
        last_progress_lines = {}

        # Log output in real-time
        while True:
            try:
                char = child.read_nonblocking(size=1, timeout=1)
                output_buffer += char

                if '\n' in output_buffer or '\r' in output_buffer:
                    lines = output_buffer.split('\n')
                    for line in lines[:-1]:
                        clean_line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', line)
                        clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                        clean_line = clean_line.strip()

                        if not clean_line:
                            continue

                        is_progress = '━' in clean_line or '%' in clean_line

                        if is_progress:
                            stream_id = None
                            if clean_line.startswith('Vid'):
                                stream_id = 'Vid'
                            elif clean_line.startswith('Aud'):
                                stream_id = 'Aud'

                            if stream_id:
                                should_log = True
                                if stream_id in last_progress_lines:
                                    last_line = last_progress_lines[stream_id]
                                    try:
                                        current_pct = float(re.search(r'(\d+\.\d+)%', clean_line).group(1))
                                        last_pct = float(re.search(r'(\d+\.\d+)%', last_line).group(1))
                                        if abs(current_pct - last_pct) < 5.0:
                                            should_log = False
                                    except:
                                        pass

                                if should_log:
                                    last_progress_lines[stream_id] = clean_line
                                    self.log(clean_line)
                        else:
                            self.log(clean_line)

                    output_buffer = lines[-1]

                if "Enter to run" in output_buffer or "Ctrl‑C to abort" in output_buffer:
                    clean_line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', output_buffer)
                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                    clean_line = clean_line.strip()
                    if clean_line:
                        self.log(clean_line)
                    self.log("[Auto-confirming - sending Enter...]")
                    child.sendline('')
                    output_buffer = ""

            except pexpect.TIMEOUT:
                if output_buffer.strip():
                    clean_line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', output_buffer)
                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                    clean_line = clean_line.strip()
                    if clean_line and '[' not in clean_line:
                        self.log(clean_line)
                    output_buffer = ""
                continue
            except pexpect.EOF:
                if output_buffer.strip():
                    clean_line = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', output_buffer)
                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                    clean_line = clean_line.strip()
                    if clean_line and '[' not in clean_line:
                        self.log(clean_line)
                break

        child.wait()
        exit_code = child.exitstatus

        self.log("=" * 60)

        if exit_code == 0:
            self.log(f"✓ Success: {self.filename}")

            try:
                if os.path.exists(self.file_path):
                    with open(self.file_path, 'r') as f:
                        cfg = json.load(f)
                        if cfg.get('deleteMe', False):
                            os.remove(self.file_path)
                            self.log(f"Deleted: {self.filename}")
            except Exception as e:
                self.log(f"Note: Could not check/delete file: {str(e)}")

            self.mark_complete(True)
        else:
            self.log(f"✗ Failed: {self.filename} (exit code: {exit_code})")
            self.mark_complete(False)


class AutoProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("allhell3 Auto Processor - Parallel Processing")
        self.root.geometry("1000x750")

        self.monitoring = False
        self.auto_process = True
        self.processed_files = set()
        self.watcher_thread = None
        self.active_tabs = []
        self.processing_queue = []  # Queue for files waiting to be processed
        self.max_parallel = 10  # Default max parallel processes

        # Platform-specific Python path
        if platform.system() == 'Windows':
            self.venv_python = "python"  # Use system python or venv if activated
        else:
            self.venv_python = os.path.expanduser("~/venvs/hellshared/bin/python3")

        self.setup_ui()
        self.main_log("Application started")
        self.main_log(f"Pending directory: {PENDING_DIR.absolute()}")
        self.main_log(f"Max parallel processes: {self.max_parallel}")
        self.main_log("Click 'Start Monitoring' to begin watching for JSON files")

        # Check browser manifest on startup
        self.check_browser_manifest_startup()

    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=X)

        title_label = ttk.Label(
            title_frame,
            text="allhell3 Auto Processor - Parallel Processing",
            font=("Arial", 16, "bold")
        )
        title_label.pack()

        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill=X, padx=10, pady=5)

        self.status_label = ttk.Label(
            status_frame,
            text="Status: Not Running",
            font=("Arial", 12, "bold"),
            foreground="red"
        )
        self.status_label.pack()

        self.dir_label = ttk.Label(
            status_frame,
            text=f"Monitoring: {PENDING_DIR.absolute()}",
            font=("Arial", 10)
        )
        self.dir_label.pack()

        # Control buttons frame
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=X)

        self.start_button = ttk.Button(
            button_frame,
            text="Start Monitoring",
            command=self.start_monitoring
        )
        self.start_button.pack(side=LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Monitoring",
            command=self.stop_monitoring,
            state=DISABLED
        )
        self.stop_button.pack(side=LEFT, padx=5)

        self.clear_button = ttk.Button(
            button_frame,
            text="Clear Main Log",
            command=self.clear_main_log
        )
        self.clear_button.pack(side=LEFT, padx=5)

        self.install_button = ttk.Button(
            button_frame,
            text="Install Dependencies",
            command=self.run_installer
        )
        self.install_button.pack(side=LEFT, padx=5)

        # Auto-process checkbox
        self.auto_var = BooleanVar(value=True)
        self.auto_checkbox = ttk.Checkbutton(
            button_frame,
            text="Auto-process (parallel)",
            variable=self.auto_var,
            command=self.toggle_auto_process
        )
        self.auto_checkbox.pack(side=LEFT, padx=20)

        # Max parallel processes control
        max_parallel_label = ttk.Label(button_frame, text="Max parallel:")
        max_parallel_label.pack(side=LEFT, padx=(20, 5))

        self.max_parallel_var = StringVar(value="10")
        self.max_parallel_spinbox = ttk.Spinbox(
            button_frame,
            from_=1,
            to=50,
            width=5,
            textvariable=self.max_parallel_var,
            command=self.update_max_parallel
        )
        self.max_parallel_spinbox.pack(side=LEFT)
        self.max_parallel_spinbox.bind('<Return>', lambda e: self.update_max_parallel())

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Main log tab (always present)
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Main Log")

        self.main_log_text = scrolledtext.ScrolledText(
            main_tab,
            wrap=WORD,
            font=("Courier New", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.main_log_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

    def main_log(self, message):
        """Log to main log tab"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        self.main_log_text.insert(END, log_line)
        self.main_log_text.see(END)
        self.main_log_text.update()

    def clear_main_log(self):
        self.main_log_text.delete(1.0, END)
        self.main_log("Main log cleared")

    def run_installer(self):
        """Launch the dependency installer GUI"""
        installer_script = Path("./dependency_installer_gui.py")

        if not installer_script.exists():
            messagebox.showerror(
                "Installer Not Found",
                "dependency_installer_gui.py not found in the current directory."
            )
            return

        self.main_log("Launching dependency installer GUI...")

        try:
            # Launch the installer GUI as a separate process
            if platform.system() == 'Windows':
                subprocess.Popen(['python', str(installer_script)])
            else:
                subprocess.Popen(['python3', str(installer_script)])

            self.main_log("✓ Dependency installer GUI launched")

        except Exception as e:
            self.main_log(f"✗ Error launching installer: {str(e)}")
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch installer:\n{str(e)}"
            )

    def check_browser_manifest(self):
        """Check if browser native messaging host is properly configured"""
        if platform.system() == 'Windows':
            # Windows: Check registry entries
            try:
                import winreg

                browsers_found = []

                # Check Chrome
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Google\Chrome\NativeMessagingHosts\org.hellyes.hellyes")
                    manifest_path, _ = winreg.QueryValueEx(key, "")
                    winreg.CloseKey(key)
                    if Path(manifest_path).exists():
                        browsers_found.append("Chrome")
                except FileNotFoundError:
                    pass

                # Check Edge
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Edge\NativeMessagingHosts\org.hellyes.hellyes")
                    manifest_path, _ = winreg.QueryValueEx(key, "")
                    winreg.CloseKey(key)
                    if Path(manifest_path).exists():
                        browsers_found.append("Edge")
                except FileNotFoundError:
                    pass

                # Check Firefox
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Mozilla\NativeMessagingHosts\org.hellyes.hellyes")
                    manifest_path, _ = winreg.QueryValueEx(key, "")
                    winreg.CloseKey(key)
                    if Path(manifest_path).exists():
                        browsers_found.append("Firefox")
                except FileNotFoundError:
                    pass

                # Check Brave
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\org.hellyes.hellyes")
                    manifest_path, _ = winreg.QueryValueEx(key, "")
                    winreg.CloseKey(key)
                    if Path(manifest_path).exists():
                        browsers_found.append("Brave")
                except FileNotFoundError:
                    pass

                return browsers_found
            except ImportError:
                return []
        else:
            # Linux/macOS: Check file locations
            browsers_found = []

            manifests = {
                "Chrome": Path.home() / ".config/google-chrome/NativeMessagingHosts/org.hellyes.hellyes.json",
                "Chromium": Path.home() / ".config/chromium/NativeMessagingHosts/org.hellyes.hellyes.json",
                "Firefox": Path.home() / ".mozilla/native-messaging-hosts/org.hellyes.hellyes.json",
                "Brave": Path.home() / ".config/BraveSoftware/Brave-Browser/NativeMessagingHosts/org.hellyes.hellyes.json",
            }

            for browser, manifest in manifests.items():
                if manifest.exists():
                    try:
                        # Verify it's valid JSON with correct structure
                        with open(manifest, 'r') as f:
                            data = json.load(f)
                            if data.get("name") == "org.hellyes.hellyes" and data.get("path"):
                                browsers_found.append(browser)
                    except:
                        pass

            return browsers_found

    def check_browser_manifest_startup(self):
        """Check browser manifest on application startup and show warning if not configured"""
        browsers_found = self.check_browser_manifest()

        if browsers_found:
            self.main_log(f"✓ Browser native messaging configured for: {', '.join(browsers_found)}")
        else:
            self.main_log("⚠ WARNING: Browser native messaging host is NOT configured!")
            self.main_log("  The browser extension will not work without this configuration.")
            self.main_log("  Click 'Install Dependencies' to set it up.")

            # Show a warning dialog
            self.root.after(1000, lambda: messagebox.showwarning(
                "Browser Extension Not Configured",
                "Browser native messaging host is not configured!\n\n"
                "The browser extension will not be able to communicate with this application.\n\n"
                "Please click 'Install Dependencies' and complete the browser manifest installation step."
            ))

    def toggle_auto_process(self):
        self.auto_process = self.auto_var.get()
        self.main_log(f"Auto-process: {'Enabled' if self.auto_process else 'Disabled'}")

    def update_max_parallel(self):
        """Update the maximum parallel processes setting"""
        try:
            new_max = int(self.max_parallel_var.get())
            if 1 <= new_max <= 50:
                self.max_parallel = new_max
                self.main_log(f"Max parallel processes updated to: {self.max_parallel}")
                # Try to process queued items if we have capacity now
                self.process_queue()
            else:
                self.main_log("Max parallel must be between 1 and 50")
                self.max_parallel_var.set(str(self.max_parallel))
        except ValueError:
            self.main_log("Invalid number for max parallel")
            self.max_parallel_var.set(str(self.max_parallel))

    def count_active_processing(self):
        """Count how many tabs are currently processing (not complete)"""
        return sum(1 for tab in self.active_tabs if not tab.is_complete)

    def process_queue(self):
        """Process queued files if we have capacity"""
        while self.processing_queue and self.count_active_processing() < self.max_parallel:
            filename, file_path = self.processing_queue.pop(0)
            self._start_processing_tab(filename, file_path)

    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.status_label.config(text="Status: Monitoring Active ✓", foreground="green")
            self.start_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self.main_log("Monitoring started")

            # Start watcher thread
            self.watcher_thread = threading.Thread(target=self.watch_directory, daemon=True)
            self.watcher_thread.start()

    def stop_monitoring(self):
        if self.monitoring:
            self.monitoring = False
            self.status_label.config(text="Status: Not Running", foreground="red")
            self.start_button.config(state=NORMAL)
            self.stop_button.config(state=DISABLED)
            self.main_log("Monitoring stopped")

    def watch_directory(self):
        """Watch directory for new JSON files"""
        self.main_log(f"Watching directory: {PENDING_DIR.absolute()}")

        while self.monitoring:
            try:
                # Look for JSON files
                json_files = list(PENDING_DIR.glob("*.json"))

                for json_file in json_files:
                    file_path = str(json_file.absolute())
                    if file_path not in self.processed_files:
                        self.processed_files.add(file_path)
                        self.main_log(f"Found new file: {json_file.name}")

                        if self.auto_process:
                            # Create a new tab and start processing (or queue it)
                            self.create_processing_tab(json_file.name, file_path)
                        else:
                            self.main_log(f"File ready: {json_file.name} (manual processing required)")

                # Check if any completed tabs freed up capacity
                self.process_queue()

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                self.main_log(f"Watcher error: {str(e)}")
                time.sleep(5)

    def create_processing_tab(self, filename, file_path):
        """Create a new tab for processing a file (or queue it if at capacity)"""
        try:
            active_count = self.count_active_processing()

            if active_count >= self.max_parallel:
                # Queue the file for later processing
                self.processing_queue.append((filename, file_path))
                self.main_log(f"Queued (at capacity {active_count}/{self.max_parallel}): {filename}")
            else:
                # Start processing immediately
                self._start_processing_tab(filename, file_path)

        except Exception as e:
            self.main_log(f"Error creating tab for {filename}: {str(e)}")

    def _start_processing_tab(self, filename, file_path):
        """Actually create and start a processing tab"""
        try:
            # Create the tab
            tab = ProcessingTab(self.notebook, filename, file_path, self.venv_python, self)
            self.active_tabs.append(tab)

            # Switch to the new tab using the widget-based index
            tab_index = tab.get_tab_index()
            if tab_index is not None:
                self.notebook.select(tab_index)

            # Start processing
            tab.start_processing()

            active_count = self.count_active_processing()
            self.main_log(f"Started processing ({active_count}/{self.max_parallel}): {filename}")

        except Exception as e:
            self.main_log(f"Error starting tab for {filename}: {str(e)}")


def main():
    root = Tk()
    app = AutoProcessorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
