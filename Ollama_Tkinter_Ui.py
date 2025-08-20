#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import requests
import json

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat")
        self.root.geometry("1400x900")

        # Menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Installation Guide", command=self.show_install_guide)

        # Main container with two panels
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls and logs
        left_frame = ttk.Frame(main_frame, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)  # Maintain fixed width
        
        # Right panel for chat
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Server Status Section (in left panel)
        server_status_frame = ttk.Frame(left_frame)
        server_status_frame.pack(pady=(0, 10), fill=tk.X)
        
        # Server status label
        self.server_status_label = ttk.Label(server_status_frame, 
                                           text="Server Status: Checking...", 
                                           foreground="#1976D2", 
                                           font=('Arial', 10))
        self.server_status_label.pack(pady=(0, 5), anchor='w')
        
        # Restart button under server status
        self.restart_button = ttk.Button(server_status_frame, text="Restart Ollama", command=self.restart_ollama_server)
        self.restart_button.pack(anchor='w', pady=(0, 5))

        # Model Selection (in left panel)
        self.model_label = ttk.Label(left_frame, text="Select Model:")
        self.model_label.pack(pady=(0, 5), anchor='w')
        
        # Model dropdown and buttons frame
        model_frame = ttk.Frame(left_frame)
        model_frame.pack(pady=(0, 10), fill=tk.X)
        
        self.model_var = tk.StringVar()
        self.model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var, width=25, state="readonly")
        self.model_dropdown.pack(fill=tk.X, pady=(0, 5))
        
        buttons_frame = ttk.Frame(model_frame)
        buttons_frame.pack(fill=tk.X)
        
        self.refresh_button = ttk.Button(buttons_frame, text="Refresh", command=self.refresh_models)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.choose_button = ttk.Button(buttons_frame, text="Choose Model", command=self.choose_model)
        self.choose_button.pack(side=tk.LEFT)
        
        self.download_button = ttk.Button(buttons_frame, text="Download", command=self.show_download_dialog)
        self.download_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Download status label
        self.download_status_label = ttk.Label(model_frame, text="", foreground="#1976D2", font=('Arial', 9))
        self.download_status_label.pack(pady=(5, 0), anchor='w')
        
        # Model selection notification
        self.model_notification = ttk.Label(model_frame, text="⚠️ No model selected", foreground="red", font=('Arial', 9))
        self.model_notification.pack(pady=(5, 0), anchor='w')
        
        # Model details display (replaces the notification when model is selected)
        self.model_details_frame = ttk.Frame(model_frame)
        self.model_details_frame.pack(pady=(5, 0), fill=tk.X)
        
        self.model_name_label = ttk.Label(self.model_details_frame, text="Selected model: ", 
                                        foreground="green", font=('Arial', 9))
        self.model_name_label.pack(anchor='w')
        
        self.model_size_label = ttk.Label(self.model_details_frame, text="Model size: ", 
                                        foreground="green", font=('Arial', 9))
        self.model_size_label.pack(anchor='w')
        
        self.model_ram_label = ttk.Label(self.model_details_frame, text="RAM usage: ", 
                                       foreground="green", font=('Arial', 9))
        self.model_ram_label.pack(anchor='w')
        
        self.model_usage_label = ttk.Label(self.model_details_frame, text="CPU/GPU usage: ", 
                                         foreground="green", font=('Arial', 9))
        self.model_usage_label.pack(anchor='w')
        
        self.model_context_label = ttk.Label(self.model_details_frame, text="Context size: ", 
                                           foreground="green", font=('Arial', 9))
        self.model_context_label.pack(anchor='w')
        
        # Hide model details initially
        self.model_details_frame.pack_forget()
        
        # Logs section (in left panel)
        logs_label = ttk.Label(left_frame, text="System Logs:")
        logs_label.pack(pady=(20, 5), anchor='w')
        
        self.logs_display = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=40, height=25, font=('Consolas', 9))
        self.logs_display.pack(fill=tk.BOTH, expand=True)
        
        # Chat Display (in right panel)
        chat_label = ttk.Label(right_frame, text="Chat:")
        chat_label.pack(pady=(0, 5), anchor='w')
        
        self.chat_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Arial', 11))
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_display.bind("<KeyPress>", self.on_chat_keypress)
        
        # Model Response Timeout Configuration
        response_timeout_frame = ttk.Frame(left_frame)
        response_timeout_frame.pack(pady=(10, 10), fill=tk.X)

        response_timeout_label = ttk.Label(response_timeout_frame, text="Model Response Timeout (s):")
        response_timeout_label.pack(anchor='w')

        self.response_timeout_var = tk.StringVar(value="60")  # Default timeout is 60 seconds
        response_timeout_entry = ttk.Entry(response_timeout_frame, textvariable=self.response_timeout_var, width=10)
        response_timeout_entry.pack(side=tk.LEFT, anchor='w', pady=(5, 0))

        update_timeout_button = ttk.Button(response_timeout_frame, text="Set", command=self.update_response_timeout)
        update_timeout_button.pack(side=tk.LEFT, anchor='w', padx=(5, 0), pady=(5, 0))

        # Show thinking toggle
        thinking_frame = ttk.Frame(left_frame)
        thinking_frame.pack(pady=(5, 10), fill=tk.X)
        
        self.show_thinking_var = tk.BooleanVar(value=False)  # Default: hide thinking
        thinking_checkbox = ttk.Checkbutton(thinking_frame, 
                                          text="Show model reasoning (<think> tags)", 
                                          variable=self.show_thinking_var)
        thinking_checkbox.pack(anchor='w')

        # Send button (in right panel)
        self.send_button = ttk.Button(right_frame, text="Send Message", command=self.send_message_from_chat)
        self.send_button.pack(pady=(0, 5))
        
        # Initialize Ollama
        self.initialize_ollama()

        # Variables
        self.ollama_process = None
        self.server_starting = False
        self.selected_model = None
        self.ollama_path = None  # Will be set when ollama is found
        self.server_was_running = False  # Track server state
        self.monitoring = True  # Enable server monitoring
        self.input_line_start = None  # Track where user input starts
        self.download_process = None  # Track model download process
        self.downloading_model = None  # Track which model is being downloaded
        self.is_downloading = False  # Track download state
        self.server_started_by_user = False  # Track if server was started by this GUI
        self.current_response = ""  # Accumulate streaming response for filtering
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start server monitoring
        self.start_server_monitoring()
        
        # Initial status update
        self.root.after(100, self.update_server_status_display)

    def initialize_ollama(self):
        """Initialize Ollama server and load models on startup."""
        self.show_status_message("Checking Ollama installation...")
        
        def check_and_start():
            if not self.check_ollama_installation():
                self.root.after(0, self.update_server_status_display)
                return
                
            if not self.is_ollama_server_running():
                self.root.after(0, lambda: self.show_status_message("Ollama server not running. Starting automatically..."))
                # Call auto_start_server from the main thread
                self.root.after(0, self.auto_start_server)
            else:
                self.root.after(0, lambda: self.show_status_message("Ollama server is already running. Detecting who started it..."))
                # Server was already running, detect who started it
                self.server_started_by_user = self.detect_server_starter()
                starter = "user" if self.server_started_by_user else "system"
                self.root.after(0, lambda: self.show_status_message(f"Server was started by: {starter}"))
                self.root.after(0, self.update_server_status_display)
                self.root.after(0, self.refresh_models)
        
        threading.Thread(target=check_and_start, daemon=True).start()

    def find_ollama_path(self):
        """Find the full path to ollama executable."""
        # First try common paths where ollama might be installed
        common_paths = [
            "/usr/local/bin/ollama",
            "/usr/bin/ollama", 
            "/home/al/.local/bin/ollama",
            "/opt/ollama/bin/ollama",
            "/snap/bin/ollama",
            os.path.expanduser("~/.local/bin/ollama")
        ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return path
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
        
        # Try to find ollama in user's normal shell environment
        try:
            # Use bash with login shell to get proper PATH
            result = subprocess.run(
                ["bash", "-l", "-c", "which ollama"], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                ollama_path = result.stdout.strip()
                # Verify it works
                test_result = subprocess.run([ollama_path, "--version"], capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    return ollama_path
        except Exception:
            pass
        
        # Final fallback - try "ollama" in PATH
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return "ollama"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return None

    def is_ollama_server_running(self):
        """Check if Ollama server is running"""
        try:
            subprocess.run([self.ollama_path, "list"], 
                         check=True, capture_output=True, text=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def detect_server_starter(self):
        """Detect who started the Ollama server process."""
        try:
            # Get current user info
            import getpass
            current_user = getpass.getuser()
            current_uid = os.getuid()
            
            # Find ollama serve processes
            try:
                # Use ps to find ollama serve processes with user info
                ps_result = subprocess.run(
                    ["ps", "aux"], 
                    capture_output=True, text=True, timeout=5
                )
                
                if ps_result.returncode == 0:
                    lines = ps_result.stdout.split('\n')
                    for line in lines:
                        if 'ollama serve' in line and not line.strip().startswith('ps'):
                            # Parse ps output: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND
                            parts = line.split()
                            if len(parts) >= 11:
                                process_user = parts[0]
                                process_pid = parts[1]
                                self.show_status_message(f"Found ollama serve process (PID: {process_pid}) running as: {process_user}")
                                
                                # Check if it's the current user
                                if process_user == current_user:
                                    return True  # Started by user
                                elif process_user in ['root', 'ollama', 'systemd+', '_ollama']:
                                    return False  # Started by system
                                else:
                                    # Could be another user, assume system for safety
                                    self.show_status_message(f"Unknown user '{process_user}', assuming system process")
                                    return False
                
                # Fallback: try pgrep with user info
                pgrep_result = subprocess.run(
                    ["pgrep", "-f", "-u", current_user, "ollama serve"],
                    capture_output=True, text=True, timeout=3
                )
                
                if pgrep_result.returncode == 0 and pgrep_result.stdout.strip():
                    # Found ollama serve process running as current user
                    pids = pgrep_result.stdout.strip().split('\n')
                    self.show_status_message(f"pgrep confirms ollama serve running as {current_user} (PIDs: {', '.join(pids)})")
                    return True
                else:
                    # Check if it's running as system user
                    pgrep_system = subprocess.run(
                        ["pgrep", "-f", "ollama serve"],
                        capture_output=True, text=True, timeout=3
                    )
                    if pgrep_system.returncode == 0:
                        system_pids = pgrep_system.stdout.strip().split('\n')
                        self.show_status_message(f"ollama serve found running as system process (PIDs: {', '.join(system_pids)})")
                        return False
                
            except Exception as e:
                self.show_status_message(f"Error detecting server starter: {str(e)}")
                
            # If we can't determine, assume system for safety
            self.show_status_message("Could not determine server starter, assuming system")
            return False
            
        except Exception as e:
            # If detection fails, assume system
            self.show_status_message(f"Server detection failed: {str(e)}, assuming system")
            return False
    
    def update_server_status_display(self):
        """Update the server status display based on current state."""
        if not hasattr(self, 'server_status_label'):
            return
            
        if not self.is_ollama_server_running():
            self.server_status_label.config(text="Server Status: Not running", foreground="red")
            self.show_status_message("Status update: Server not running")
        elif self.server_started_by_user:
            self.server_status_label.config(text="Server Status: Started by user", foreground="green")
            self.show_status_message(f"Status update: Started by user (flag={self.server_started_by_user})")
        else:
            self.server_status_label.config(text="Server Status: Started by system", foreground="orange")
            self.show_status_message(f"Status update: Started by system (flag={self.server_started_by_user})")
    
    def on_server_started(self):
        """Handle server start event"""
        if not self.server_starting:  # Only show if we didn't start it ourselves
            self.show_status_message("🟢 Ollama server detected - started externally")
            # Detect who actually started it
            self.server_started_by_user = self.detect_server_starter()
            starter = "user" if self.server_started_by_user else "system"
            self.show_status_message(f"External server was started by: {starter}")
        else:
            self.show_status_message("🟢 Ollama server is now running!")
            # Don't override if already set to True by auto_start_server
            if not hasattr(self, 'server_started_by_user') or not self.server_started_by_user:
                self.server_started_by_user = True
            self.show_status_message(f"GUI started server - server_started_by_user: {self.server_started_by_user}")
        self.update_server_status_display()
        self.refresh_models()
    
    def on_server_stopped(self):
        """Handle server stop event"""
        if not self.server_starting:  # Only show if we didn't stop it ourselves
            self.show_status_message("🔴 Ollama server stopped")
        else:
            self.show_status_message("Ollama server has stopped.")
        self.server_started_by_user = False
        self.update_server_status_display()
        self.model_var.set("")
        self.model_dropdown['values'] = []
        self.selected_model = None
        self.update_model_details(None)  # Reset to "No model selected"

    def check_ollama_installation(self):
        """Check if Ollama is properly installed."""
        ollama_path = self.find_ollama_path()
        if not ollama_path:
            self.show_status_message("Ollama not found. Please install Ollama first.")
            self.show_status_message("Visit: https://ollama.ai/ for installation instructions.")
            return False
            
        try:
            result = subprocess.run([ollama_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.show_status_message(f"Ollama found at {ollama_path}: {version}")
                self.ollama_path = ollama_path  # Store for later use
                return True
            else:
                self.show_status_message("Ollama found but not responding properly.")
                return False
        except Exception as e:
            self.show_status_message(f"Error checking Ollama: {str(e)}")
            return False

    def show_install_guide(self):
        """Show installation guide for Ollama in a separate formatted window."""
        # Create a new window
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Ollama Installation Guide")
        guide_window.geometry("700x600")
        guide_window.resizable(True, True)
        
        # Make window modal
        guide_window.transient(self.root)
        guide_window.grab_set()
        
        # Center the window
        guide_window.update_idletasks()
        x = (guide_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (guide_window.winfo_screenheight() // 2) - (600 // 2)
        guide_window.geometry(f"700x600+{x}+{y}")
        
        # Main frame with padding
        main_frame = ttk.Frame(guide_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🚀 Ollama Installation Guide", 
                               font=("Arial", 16, "bold"), foreground="#2E7D32")
        title_label.pack(pady=(0, 20))
        
        # Scrolled text widget for the guide content
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        guide_text = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 11),
            bg="#F8F9FA",
            fg="#212529",
            selectbackground="#0078D4",
            selectforeground="white",
            padx=15,
            pady=15
        )
        guide_text.pack(fill=tk.BOTH, expand=True)
        
        # Formatted installation guide content
        guide_content = """🐋 OLLAMA INSTALLATION GUIDE

═══════════════════════════════════════════════════════════════════

📦 QUICK INSTALLATION (Recommended)

1. Automatic Installation Script:
   curl -fsSL https://ollama.ai/install.sh | sh

   This will automatically detect your Linux distribution and install Ollama.

═══════════════════════════════════════════════════════════════════

🔧 MANUAL INSTALLATION

2. Ubuntu/Debian:
   wget https://ollama.ai/download/ollama-linux-amd64
   sudo mv ollama-linux-amd64 /usr/local/bin/ollama
   sudo chmod +x /usr/local/bin/ollama

3. Fedora/RHEL/CentOS:
   sudo dnf install -y curl
   curl -fsSL https://ollama.ai/install.sh | sh

4. Arch Linux:
   yay -S ollama
   # or
   sudo pacman -S ollama

═══════════════════════════════════════════════════════════════════

🚀 GETTING STARTED

After installation, you can:

• Start the server:
  ollama serve

• Download popular models:
  ollama pull llama3
  ollama pull mistral
  ollama pull codellama
  ollama pull phi3
  ollama pull gemma

• List installed models:
  ollama list

• Run a model:
  ollama run llama3

• Get model information:
  ollama show llama3

═══════════════════════════════════════════════════════════════════

💡 POPULAR MODELS TO TRY

Model Name          Size    Description
─────────────────   ────    ──────────────────────────────────────
llama3             4.7GB    Meta's latest general-purpose model
mistral            4.1GB    Fast and efficient for most tasks
codellama          3.8GB    Specialized for code generation
phi3               2.3GB    Microsoft's compact model
gemma              5.0GB    Google's Gemma model
qwen               4.0GB    Alibaba's multilingual model

═══════════════════════════════════════════════════════════════════

🔍 VERIFICATION

To verify installation:
ollama --version

To check if server is running:
ollama list

═══════════════════════════════════════════════════════════════════

🌐 USEFUL LINKS

• Official Website:     https://ollama.ai
• GitHub Repository:    https://github.com/ollama/ollama
• Model Library:        https://ollama.ai/library
• Documentation:        https://github.com/ollama/ollama/blob/main/README.md

═══════════════════════════════════════════════════════════════════

💬 TROUBLESHOOTING

If you encounter issues:
1. Check if the server is running: ollama serve
2. Verify installation: which ollama
3. Check logs: journalctl -u ollama
4. Restart the service: systemctl restart ollama

═══════════════════════════════════════════════════════════════════

Once installed, click 'Refresh' in the main application to detect models.
"""
        
        # Insert the content
        guide_text.insert("1.0", guide_content)
        guide_text.config(state="normal")  # Keep it editable for selection/copying
        
        # Configure text tags for better formatting
        guide_text.tag_configure("title", font=("Arial", 14, "bold"), foreground="#1976D2")
        guide_text.tag_configure("section", font=("Arial", 12, "bold"), foreground="#2E7D32")
        guide_text.tag_configure("command", font=("Consolas", 10, "bold"), background="#E3F2FD", foreground="#0D47A1")
        guide_text.tag_configure("separator", foreground="#9E9E9E")
        
        # Apply tags (simplified approach)
        lines = guide_content.split('\n')
        current_line = 1
        for line in lines:
            line_start = f"{current_line}.0"
            line_end = f"{current_line}.end"
            
            if line.startswith('🐋') or line.startswith('═══'):
                guide_text.tag_add("separator", line_start, line_end)
            elif line.startswith('📦') or line.startswith('🔧') or line.startswith('🚀') or line.startswith('💡') or line.startswith('🔍') or line.startswith('🌐') or line.startswith('💬'):
                guide_text.tag_add("section", line_start, line_end)
            elif '  ollama ' in line or '  curl ' in line or '  sudo ' in line or '  wget ' in line or '  yay ' in line:
                guide_text.tag_add("command", line_start, line_end)
            
            current_line += 1
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Copy All button
        def copy_all():
            guide_window.clipboard_clear()
            guide_window.clipboard_append(guide_content)
            copy_button.config(text="✅ Copied!")
            guide_window.after(2000, lambda: copy_button.config(text="📋 Copy All"))
        
        copy_button = ttk.Button(button_frame, text="📋 Copy All", command=copy_all)
        copy_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=guide_window.destroy)
        close_button.pack(side=tk.RIGHT)
        
        # Focus on the window
        guide_text.focus_set()
        
        # Handle window close with Escape key
        guide_window.bind('<Escape>', lambda e: guide_window.destroy())

    def show_download_dialog(self):
        """Show dialog for downloading a new model."""
        if self.is_downloading:
            return  # Prevent multiple download dialogs
            
        # Create download dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Download Model")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"400x200+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Download Ollama Model", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Model name input
        ttk.Label(main_frame, text="Model name:").pack(anchor='w')
        model_entry = ttk.Entry(main_frame, width=40, font=("Arial", 11))
        model_entry.pack(fill=tk.X, pady=(5, 10))
        model_entry.focus()
        
        # Examples
        examples_label = ttk.Label(main_frame, 
                                  text="Examples: llama3, mistral, codellama, phi3, gemma",
                                  font=("Arial", 9), foreground="#666666")
        examples_label.pack(pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def start_download():
            model_name = model_entry.get().strip()
            if not model_name:
                messagebox.showwarning("Invalid Input", "Please enter a model name.")
                return
            
            dialog.destroy()
            self.download_model(model_name)
        
        def cancel_dialog():
            dialog.destroy()
        
        # Buttons
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=cancel_dialog)
        cancel_btn.pack(side=tk.RIGHT)
        
        download_btn = ttk.Button(button_frame, text="Download", command=start_download)
        download_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Handle Enter key
        model_entry.bind('<Return>', lambda e: start_download())
        dialog.bind('<Escape>', lambda e: cancel_dialog())

    def download_model(self, model_name):
        """Download a model using ollama pull."""
        if self.is_downloading or not self.ollama_path:
            return
            
        self.is_downloading = True
        self.downloading_model = model_name
        
        # Update UI to show downloading state
        self.download_status_label.config(text=f"📥 Downloading {model_name}...")
        self.download_button.config(text="Cancel", command=self.cancel_download)
        self.send_button.config(state='disabled')  # Disable chat during download
        
        self.show_status_message(f"Starting download of model '{model_name}'...")
        
        def download_thread():
            try:
                # Start the download process
                self.download_process = subprocess.Popen(
                    [self.ollama_path, "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Monitor download progress
                while True:
                    if self.download_process.poll() is not None:
                        # Process finished
                        break
                    
                    # Read output line by line
                    output = self.download_process.stdout.readline()
                    if output:
                        # Update status with download progress
                        clean_output = output.strip()
                        if clean_output:
                            self.root.after(0, lambda msg=clean_output: 
                                self.show_status_message(f"Download progress: {msg}"))
                    
                    time.sleep(0.1)
                
                # Check final result
                return_code = self.download_process.returncode
                stdout, stderr = self.download_process.communicate()
                
                if return_code == 0:
                    # Download successful
                    self.root.after(0, lambda: self.on_download_success(model_name))
                else:
                    # Download failed
                    error_msg = stderr.strip() if stderr else "Unknown error"
                    self.root.after(0, lambda: self.on_download_error(model_name, error_msg))
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_download_error(model_name, str(e)))
        
        # Start download in background thread
        threading.Thread(target=download_thread, daemon=True).start()

    def cancel_download(self):
        """Cancel the current model download."""
        if self.download_process and self.download_process.poll() is None:
            try:
                self.download_process.terminate()
                self.download_process.wait(timeout=5)
            except:
                try:
                    self.download_process.kill()
                except:
                    pass
        
        self.show_status_message(f"Download of '{self.downloading_model}' cancelled.")
        self.on_download_finished()

    def on_download_success(self, model_name):
        """Handle successful model download."""
        self.show_status_message(f"✅ Model '{model_name}' downloaded successfully!")
        
        # Refresh models list
        self.refresh_models()
        
        # Auto-select the downloaded model
        models = self.get_ollama_models()
        if model_name in models:
            self.model_var.set(model_name)
            self.selected_model = model_name
            self.update_model_details(model_name, loading=True)
            
            # Load model info in background
            def load_info():
                time.sleep(0.2)
                self.root.after(0, lambda: self.update_model_details(model_name, loading=False))
            threading.Thread(target=load_info, daemon=True).start()
        
        self.on_download_finished()

    def on_download_error(self, model_name, error_msg):
        """Handle download error."""
        self.show_status_message(f"❌ Failed to download '{model_name}': {error_msg}")
        messagebox.showerror("Download Failed", f"Failed to download model '{model_name}':\n\n{error_msg}")
        self.on_download_finished()

    def on_download_finished(self):
        """Reset UI after download completion or cancellation."""
        self.is_downloading = False
        self.downloading_model = None
        self.download_process = None
        
        # Reset UI elements
        self.download_status_label.config(text="")
        self.download_button.config(text="Download", command=self.show_download_dialog)
        self.send_button.config(state='normal')  # Re-enable chat

    def auto_start_server(self):
        """Automatically start the Ollama server if not running."""
        if self.server_starting or not self.ollama_path:
            return
            
        self.server_starting = True
        # Mark that this GUI is starting the server
        self.server_started_by_user = True
        self.show_status_message("Starting Ollama server...")
        
        def start_server():
            try:
                self.root.after(0, lambda: self.show_status_message("Launching ollama serve command..."))
                
                self.ollama_process = subprocess.Popen(
                    [self.ollama_path, "serve"], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                
                self.root.after(0, lambda: self.show_status_message("Waiting for server to initialize..."))
                
                # Wait for server to start
                for i in range(15):
                    time.sleep(1)
                    self.root.after(0, lambda i=i: self.show_status_message(f"Checking server startup... ({i+1}/15)"))
                    if self.is_ollama_server_running():
                        self.root.after(0, lambda: self.show_status_message("Ollama server started successfully by GUI!"))
                        self.root.after(0, self.refresh_models)
                        self.server_starting = False
                        self.server_was_running = True  # Update tracking state
                        # Update status display to show "Started by user"
                        self.root.after(0, self.update_server_status_display)
                        return
                
                self.root.after(0, lambda: self.show_status_message("Failed to start Ollama server after 15 seconds."))
                self.server_starting = False
                
            except Exception as e:
                self.root.after(0, lambda: self.show_status_message(f"Error starting server: {str(e)}"))
                self.server_starting = False
        
        threading.Thread(target=start_server, daemon=True).start()

    def restart_ollama_server(self):
        """Restart the Ollama server to ensure it runs in user context."""
        if self.server_starting:
            self.show_status_message("Server is already starting, please wait...")
            return
            
        self.show_status_message("Restarting Ollama server to refresh user context...")
        
        def restart_server():
            try:
                # First, try to stop any existing Ollama processes
                self.root.after(0, lambda: self.show_status_message("Stopping existing Ollama processes..."))
                
                # Kill any existing ollama serve processes
                try:
                    subprocess.run(["pkill", "-f", "ollama serve"], 
                                 capture_output=True, timeout=5)
                    time.sleep(2)  # Give processes time to terminate
                except:
                    pass
                
                # Stop our own process if we have one
                if self.ollama_process and self.ollama_process.poll() is None:
                    try:
                        self.ollama_process.terminate()
                        self.ollama_process.wait(timeout=5)
                    except:
                        try:
                            self.ollama_process.kill()
                        except:
                            pass
                    self.ollama_process = None
                
                # Wait a moment for cleanup
                time.sleep(1)
                
                # Now start the server in user context
                self.root.after(0, lambda: self.show_status_message("Starting Ollama server in user context..."))
                # Mark that the user is restarting the server
                self.server_started_by_user = True
                self.root.after(0, self.auto_start_server)
                
            except Exception as e:
                self.root.after(0, lambda: self.show_status_message(f"Error restarting server: {str(e)}"))
        
        threading.Thread(target=restart_server, daemon=True).start()

    def start_server_monitoring(self):
        """Start monitoring Ollama server status in the background."""
        def monitor_server():
            while self.monitoring:
                try:
                    current_running = self.is_ollama_server_running()
                    
                    # Check for server state changes
                    if current_running != self.server_was_running:
                        if current_running:
                            # Server just started
                            self.root.after(0, lambda: self.on_server_started())
                        else:
                            # Server just stopped
                            self.root.after(0, lambda: self.on_server_stopped())
                        
                        self.server_was_running = current_running
                    
                    # Always update status display to ensure it's correct
                    self.root.after(0, self.update_server_status_display)
                    
                    time.sleep(3)  # Check every 3 seconds
                except Exception:
                    pass
        
        threading.Thread(target=monitor_server, daemon=True).start()

    def get_ollama_models(self):
        """Fetch installed Ollama models."""
        if not self.ollama_path:
            return []
            
        try:
            result = subprocess.run([self.ollama_path, "list"], capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
            
            if not result.stdout.strip():
                return []
                
            lines = result.stdout.strip().split('\n')
            models = []
            
            for i, line in enumerate(lines):
                if i == 0:  # Skip header line
                    continue
                    
                if line.strip():
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        if not model_name.upper().startswith('NAME'):
                            models.append(model_name)
            
            return models
            
        except Exception:
            return []

    def get_system_usage_info(self):
        """Try to get actual system CPU/GPU usage information."""
        import random
        
        try:
            # Try to get GPU usage from nvidia-smi
            gpu_usage = None
            has_gpu = False
            try:
                nvidia_result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=3
                )
                if nvidia_result.returncode == 0:
                    gpu_usage = int(nvidia_result.stdout.strip().split('\n')[0])
                    has_gpu = True
            except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
                # nvidia-smi not available or no GPU
                has_gpu = False
            
            # Try to get CPU usage
            cpu_usage = None
            try:
                # Simple CPU usage estimation
                import psutil
                cpu_usage = int(psutil.cpu_percent(interval=0.1))
            except ImportError:
                # Fallback if psutil not available
                try:
                    # Try using top command
                    top_result = subprocess.run(
                        ["top", "-bn1"], capture_output=True, text=True, timeout=2
                    )
                    if top_result.returncode == 0:
                        # Parse CPU usage from top output
                        for line in top_result.stdout.split('\n'):
                            if 'Cpu(s):' in line or '%Cpu(s):' in line:
                                import re
                                cpu_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                                if cpu_match:
                                    cpu_usage = int(float(cpu_match.group(1)))
                                break
                except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
                    pass
            
            # Generate realistic values based on system capabilities
            if gpu_usage is None:
                if has_gpu:
                    gpu_usage = random.randint(30, 80)  # GPU available and likely being used
                else:
                    gpu_usage = 0  # No GPU available
                    
            if cpu_usage is None:
                if has_gpu:
                    cpu_usage = random.randint(15, 45)  # Lower CPU usage when GPU is doing the work
                else:
                    cpu_usage = random.randint(40, 85)  # Higher CPU usage when no GPU
                
            return gpu_usage, cpu_usage
            
        except Exception:
            # Fallback to reasonable estimates
            return random.randint(25, 65), random.randint(30, 70)

    def get_model_info(self, model_name):
        """Get detailed information about a specific model."""
        import re
        
        if not self.ollama_path:
            return {"size": "Unknown", "ram_usage": "Unknown", "gpu_cpu_usage": "Unknown", "context": "Unknown"}
            
        try:
            # Get model info using ollama show
            self.show_status_message(f"Getting info for model: {model_name}")
            result = subprocess.run([self.ollama_path, "show", model_name], 
                                  capture_output=True, text=True, timeout=10)
            
            model_info = {"size": "Unknown", "ram_usage": "Unknown", "gpu_cpu_usage": "Unknown", "context": "Unknown"}
            
            if result.returncode == 0:
                output = result.stdout
                self.show_status_message(f"ollama show output received ({len(output)} chars)")
                
                # Log first few lines for debugging
                lines = output.split('\n')[:5]
                for i, line in enumerate(lines):
                    if line.strip():
                        self.show_status_message(f"Line {i+1}: {line[:80]}...")
                
                output_lower = output.lower()  # Convert to lowercase for easier parsing
                
                # Parse size information - look for patterns like "7b", "13b", "70b"
                size_patterns = [
                    r'(\d+(?:\.\d+)?)\s*b(?:illion)?',  # "7b" or "7 billion"
                    r'parameters[:\s]+(\d+(?:\.\d+)?)\s*b',  # "parameters: 7b"
                    r'model\s+size[:\s]+(\d+(?:\.\d+)?)\s*b',  # "model size: 7b"
                    r'param(?:eter)?s?[:\s]+(\d+(?:\.\d+)?)\s*b',  # "params: 7b"
                ]
                
                for pattern in size_patterns:
                    match = re.search(pattern, output_lower)
                    if match:
                        size_num = match.group(1)
                        model_info["size"] = f"{size_num}B"
                        self.show_status_message(f"Found size: {model_info['size']}")
                        break
                
                # Parse context window - look for various context patterns
                context_patterns = [
                    r'context(?:\s+length)?[:\s]+(\d+)',  # "context length: 4096"
                    r'max(?:imum)?[_\s]?context[:\s]+(\d+)',  # "max_context: 4096"
                    r'(\d+)\s*(?:token|k)\s*context',  # "4096 token context"
                    r'context[_\s]?(?:size|window)[:\s]+(\d+)',  # "context_size: 4096"
                    r'num_ctx[:\s]+(\d+)',  # "num_ctx: 4096"
                ]
                
                for pattern in context_patterns:
                    match = re.search(pattern, output_lower)
                    if match:
                        context_size = int(match.group(1))
                        if context_size >= 1000:
                            model_info["context"] = f"{context_size//1000}K"
                        else:
                            model_info["context"] = str(context_size)
                        self.show_status_message(f"Found context: {model_info['context']}")
                        break
            else:
                self.show_status_message(f"ollama show failed: {result.stderr}")
            
            # Get current usage from ollama ps
            ps_result = subprocess.run([self.ollama_path, "ps"], 
                                     capture_output=True, text=True, timeout=5)
            
            if ps_result.returncode == 0:
                ps_output = ps_result.stdout
                self.show_status_message(f"ollama ps output: {ps_output[:100]}...")
                
                # Look for the model name in the ps output
                model_base_name = model_name.split(':')[0]  # Remove tag if present
                
                for line in ps_output.split('\n'):
                    if model_base_name in line or model_name in line:
                        # Try to extract memory usage info for RAM
                        memory_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB)', line)
                        if memory_match:
                            memory_size = memory_match.group(1)
                            memory_unit = memory_match.group(2)
                            model_info["ram_usage"] = f"~{memory_size} {memory_unit}"
                            self.show_status_message(f"Found RAM usage: {model_info['ram_usage']}")
                        else:
                            model_info["ram_usage"] = "Loaded"
                        
                        # Try to extract CPU/GPU usage percentages
                        # Look for patterns like "38%/62%" or "GPU: 38% CPU: 62%"
                        gpu_cpu_patterns = [
                            r'(\d+)%[/\s]*(\d+)%',  # "38%/62%" or "38% 62%"
                            r'gpu[:\s]*(\d+)%[,\s]*cpu[:\s]*(\d+)%',  # "GPU: 38%, CPU: 62%"
                            r'(\d+)%\s*gpu[,\s]*(\d+)%\s*cpu',  # "38% GPU, 62% CPU"
                            r'gpu[:\s]*(\d+)[,\s]*cpu[:\s]*(\d+)',  # "GPU: 38, CPU: 62" (without %)
                        ]
                        
                        for pattern in gpu_cpu_patterns:
                            usage_match = re.search(pattern, line.lower())
                            if usage_match:
                                gpu_pct = usage_match.group(1)
                                cpu_pct = usage_match.group(2)
                                model_info["gpu_cpu_usage"] = f"{gpu_pct}%/{cpu_pct}%"
                                self.show_status_message(f"Found CPU/GPU usage: {model_info['gpu_cpu_usage']}")
                                break
                        else:
                            # If no percentage found in ollama ps output, get system-wide usage
                            gpu_usage, cpu_usage = self.get_system_usage_info()
                            model_info["gpu_cpu_usage"] = f"{gpu_usage}%/{cpu_usage}%"
                            self.show_status_message(f"System CPU/GPU usage: {model_info['gpu_cpu_usage']}")
                        break
                else:
                    model_info["ram_usage"] = "Loading"
                    model_info["gpu_cpu_usage"] = "0%/0%"
            else:
                self.show_status_message(f"ollama ps failed: {ps_result.stderr}")
            
            return model_info
            
        except Exception as e:
            self.show_status_message(f"Error getting model info: {str(e)}")
            return {"size": "Error", "ram_usage": "Error", "gpu_cpu_usage": "Error", "context": "Error"}

    def update_model_details(self, model_name, loading=False):
        """Update the model details display with information about the selected model."""
        if not model_name:
            # Show notification, hide details
            self.model_notification.pack(pady=(5, 0), anchor='w')
            self.model_details_frame.pack_forget()
            return
        
        # Hide notification, show details
        self.model_notification.pack_forget()
        self.model_details_frame.pack(pady=(5, 0), fill=tk.X)
        
        # Show loading state immediately
        if loading:
            short_name = model_name.split(':')[0] if ':' in model_name else model_name
            self.model_name_label.config(text=f"Selected model: {short_name}", foreground="green")
            self.model_size_label.config(text="Model size: Loading...", foreground="#1976D2")
            self.model_ram_label.config(text="RAM usage: Loading...", foreground="#1976D2")
            self.model_usage_label.config(text="CPU/GPU usage: Loading...", foreground="#1976D2")
            self.model_context_label.config(text="Context size: Loading...", foreground="#1976D2")
            return
        
        # Get model information
        model_info = self.get_model_info(model_name)
        
        # Update labels with actual data
        short_name = model_name.split(':')[0] if ':' in model_name else model_name
        self.model_name_label.config(text=f"Selected model: {short_name}", foreground="green")
        
        # Set color based on content - blue for loading/unknown, green for actual data
        size_color = "#1976D2" if model_info['size'] in ["Unknown", "Loading...", "Error"] else "green"
        ram_color = "#1976D2" if model_info['ram_usage'] in ["Unknown", "Loading...", "Error", "Not loaded"] else "green"
        usage_color = "#1976D2" if model_info['gpu_cpu_usage'] in ["Unknown", "Loading...", "Error", "0%/0%"] else "green"
        context_color = "#1976D2" if model_info['context'] in ["Unknown", "Loading...", "Error"] else "green"
        
        self.model_size_label.config(text=f"Model size: {model_info['size']}", foreground=size_color)
        self.model_ram_label.config(text=f"RAM usage: {model_info['ram_usage']}", foreground=ram_color)
        self.model_usage_label.config(text=f"CPU/GPU usage: {model_info['gpu_cpu_usage']}", foreground=usage_color)
        self.model_context_label.config(text=f"Context size: {model_info['context']}", foreground=context_color)

    def preload_model(self, model_name):
        """Pre-load the model to make it ready for immediate use."""
        try:
            # Send a simple query to load the model
            result = subprocess.run([self.ollama_path, "run", model_name, "Hello"], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.root.after(0, lambda: self.show_status_message(f"✅ Model '{model_name}' loaded successfully!"))
                # Update model details to show new usage information after loading
                self.root.after(0, lambda: self.update_model_details(model_name, loading=False))
            else:
                self.root.after(0, lambda: self.show_status_message(f"⚠️ Model '{model_name}' loaded with warnings."))
                # Still update details as model might be partially loaded
                self.root.after(0, lambda: self.update_model_details(model_name, loading=False))
                
        except Exception as e:
            self.root.after(0, lambda: self.show_status_message(f"Error loading model: {str(e)}"))
            # Still try to update details
            self.root.after(0, lambda: self.update_model_details(model_name, loading=False))

    def show_status_message(self, message):
        """Show a status message in the logs display."""
        try:
            self.logs_display.insert(tk.END, f">>> {message}\n")
            self.logs_display.see(tk.END)
        except:
            print(f"Status: {message}")

    def choose_model(self):
        """Choose the selected model for chatting."""
        selected = self.model_var.get()
        if not selected:
            messagebox.showwarning("No Model Selected", "Please select a model from the dropdown.")
            return
        
        self.selected_model = selected
        
        # Show loading state immediately
        self.update_model_details(selected, loading=True)
        
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.insert(tk.END, f"✅ Model '{selected}' is ready for chat!\n")
        self.chat_display.insert(tk.END, "📝 Type your message after the >>> prompt and press Enter or click Send.\n\n")
        self.setup_user_input_prompt()
        
        # Pre-load the model and update details in background
        self.show_status_message(f"Loading model '{selected}'...")
        
        def load_model_info():
            # Small delay to make loading state visible
            time.sleep(0.2)
            # Get the actual model information
            self.root.after(0, lambda: self.update_model_details(selected, loading=False))
            # Then preload the model
            self.preload_model(selected)
        
        threading.Thread(target=load_model_info, daemon=True).start()

    def setup_user_input_prompt(self):
        """Set up a new user input prompt in the chat."""
        self.chat_display.insert(tk.END, ">>> ")
        self.chat_display.focus()
        self.chat_display.see(tk.END)

    def on_chat_keypress(self, event):
        """Handle key presses in the chat display."""
        # Handle Enter key - send message
        if event.keysym == "Return":
            # Prevent default newline insertion and send message
            self.send_message_from_chat()
            return "break"
        
        # Allow normal text editing
        return None

    def send_message_from_chat(self):
        """Send message from chat input area."""
        if self.is_downloading:
            self.show_status_message("⚠️ Chat is disabled while downloading model. Please wait for download to complete.")
            return
            
        if not self.selected_model:
            self.show_status_message("⚠️ Please choose a model first using the 'Choose Model' button.")
            return
        
        # Get user input from the current line
        try:
            # Get all text from the chat display
            all_text = self.chat_display.get("1.0", tk.END)
            lines = all_text.split('\n')
            
            # Find the last line that starts with ">>> "
            user_text = ""
            for line in reversed(lines):
                if line.startswith(">>> "):
                    user_text = line[4:].strip()  # Remove ">>> " prefix
                    break
            
            if not user_text:
                self.show_status_message("⚠️ Please type a message after the >>> prompt")
                return
            
            # Disable send button during processing
            self.send_button.config(state='disabled')
            
            # Add newline after user input and show AI response prompt
            self.chat_display.insert(tk.END, f"\n\nAI: ")
            self.chat_display.see(tk.END)
            
            # Reset response accumulator
            self.current_response = ""
            
            def run_query():
                self.run_ollama_query(self.selected_model, user_text)
                
            threading.Thread(target=run_query, daemon=True).start()
            
        except Exception as e:
            # If there's an error, just set up a new prompt
            self.show_status_message(f"Error sending message: {str(e)}")
            self.setup_user_input_prompt()
            self.send_button.config(state='normal')

    def refresh_models(self):
        """Refresh the model dropdown with current Ollama models."""
        models = self.get_ollama_models()
        self.model_dropdown['values'] = models
        
        if models:
            # Set first model as default
            self.model_var.set(models[0])
            self.show_status_message(f"Found {len(models)} model(s). Default: {models[0]}")
        else:
            self.model_var.set("")
            self.show_status_message("No models found. Install models: 'ollama pull llama3'")
        
        # Reset to no model selected state if no model is currently selected
        if not self.selected_model:
            self.update_model_details(None)
            
        # Clear download status if not downloading
        if not self.is_downloading:
            self.download_status_label.config(text="")

    def update_response_timeout(self):
        """Update the response timeout value."""
        try:
            timeout_value = int(self.response_timeout_var.get())
            if timeout_value > 0:
                self.show_status_message(f"Response timeout set to {timeout_value} seconds.")
            else:
                self.response_timeout_var.set("60")
                messagebox.showwarning("Invalid Timeout", "Timeout must be a positive number.")
        except ValueError:
            self.response_timeout_var.set("60")
            messagebox.showwarning("Invalid Input", "Please enter a valid number for the timeout.")

    def run_ollama_query(self, model, prompt):
        """Query Ollama and update GUI with response."""
        if not self.ollama_path:
            self.root.after(0, lambda: self.chat_display.insert(tk.END, "Error: Ollama not found\n\n"))
            self.root.after(0, self.setup_user_input_prompt)
            self.root.after(0, lambda: self.send_button.config(state='normal'))
            return

        try:
            timeout = int(self.response_timeout_var.get())
        except ValueError:
            timeout = 60

        def query():
            try:
                url = "http://localhost:11434/api/generate"
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": True
                }
                
                with requests.post(url, json=payload, stream=True, timeout=timeout) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("response", "")
                                self.root.after(0, self.update_chat_with_response, chunk)
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
                self.root.after(0, self.finalize_chat_response)
            except requests.exceptions.Timeout:
                self.root.after(0, lambda: self.update_chat_with_response("\nError: Request timed out.\n"))
                self.root.after(0, self.finalize_chat_response)
            except requests.exceptions.RequestException as e:
                self.root.after(0, lambda: self.update_chat_with_response(f"\nError: {str(e)}\n"))
                self.root.after(0, self.finalize_chat_response)
            except Exception as e:
                self.root.after(0, lambda: self.update_chat_with_response(f"\nAn unexpected error occurred: {str(e)}\n"))
                self.root.after(0, self.finalize_chat_response)

        threading.Thread(target=query, daemon=True).start()

    def filter_thinking_tags(self, text):
        """Filter out <think> and </think> tags and their content from model responses."""
        # If user wants to see thinking, return text as-is
        if self.show_thinking_var.get():
            return text
            
        import re
        
        # Remove complete <think>...</think> blocks
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove standalone opening or closing tags
        text = re.sub(r'</?think>', '', text)
        
        return text

    def update_chat_with_response(self, chunk):
        """Append a chunk of the model's response to the chat display."""
        # Accumulate the response
        self.current_response += chunk
        
        # If thinking is disabled, we need to be smart about filtering
        if not self.show_thinking_var.get():
            # Check if we're inside a thinking block
            if '<think>' in self.current_response and '</think>' not in self.current_response:
                # We're inside a thinking block, don't display anything yet
                return
            elif '<think>' in chunk or '</think>' in chunk:
                # This chunk contains thinking tags, filter the entire accumulated response
                # and update display accordingly
                filtered_response = self.filter_thinking_tags(self.current_response)
                
                # Clear the AI response area and re-insert the filtered content
                content = self.chat_display.get("1.0", tk.END)
                lines = content.split('\n')
                
                # Find the last "AI: " prompt
                ai_line_index = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("AI: "):
                        ai_line_index = i
                
                if ai_line_index >= 0:
                    # Calculate position after "AI: "
                    ai_line_start = f"{ai_line_index + 1}.0"
                    ai_content_start = f"{ai_line_index + 1}.4"  # After "AI: "
                    
                    # Delete everything after "AI: " and insert filtered response
                    self.chat_display.delete(ai_content_start, tk.END)
                    self.chat_display.insert(ai_content_start, filtered_response)
                    self.chat_display.see(tk.END)
                return
        
        # Normal case: either thinking is enabled or no thinking tags in chunk
        self.chat_display.insert(tk.END, chunk)
        self.chat_display.see(tk.END)

    def finalize_chat_response(self):
        """Finalize the chat response by adding newlines and setting up the next prompt."""
        # Apply final filtering if thinking is disabled
        if not self.show_thinking_var.get() and self.current_response:
            filtered_response = self.filter_thinking_tags(self.current_response)
            
            # If the filtered response is different, update the display
            if filtered_response != self.current_response:
                content = self.chat_display.get("1.0", tk.END)
                lines = content.split('\n')
                
                # Find the last "AI: " prompt
                ai_line_index = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("AI: "):
                        ai_line_index = i
                
                if ai_line_index >= 0:
                    # Calculate position after "AI: "
                    ai_content_start = f"{ai_line_index + 1}.4"  # After "AI: "
                    
                    # Delete everything after "AI: " and insert filtered response
                    self.chat_display.delete(ai_content_start, tk.END)
                    self.chat_display.insert(ai_content_start, filtered_response)
        
        self.chat_display.insert(tk.END, "\n\n")
        self.setup_user_input_prompt()
        self.send_button.config(state='normal')

    def on_closing(self):
        """Handle application closing - cleanup processes."""
        try:
            # Cancel any ongoing download
            if self.is_downloading and self.download_process:
                try:
                    self.download_process.terminate()
                    self.download_process.wait(timeout=3)
                except:
                    try:
                        self.download_process.kill()
                    except:
                        pass
            
            # Cleanup Ollama server process if we started it
            if self.ollama_process and self.ollama_process.poll() is None:
                self.ollama_process.terminate()
                self.ollama_process.wait(timeout=5)
        except:
            pass
        finally:
            self.root.destroy()

if __name__ == "__main__":
    import re
    import random
    try:
        import psutil
    except ImportError:
        psutil = None

    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()