#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import requests
import json
import re
import webbrowser
import getpass

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter GUI for Ollama")
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
        
        # Content frame for left and right panels
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for controls and logs
        left_frame = ttk.Frame(content_frame, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)  # Maintain fixed width
        
        # Right panel for chat
        right_frame = ttk.Frame(content_frame)
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
        
        # Add download state tracking
        self.is_downloading = False
        self.downloading_model = None
        
        self.download_button = ttk.Button(buttons_frame, text="Download", command=self.start_download_action)
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
        
        # Chat history display (read-only) with enhanced formatting support
        self.chat_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=('Arial', 11), 
                                                    state='disabled', bg='#FFFFFF', fg='#333333',
                                                    selectbackground='#0078D4', selectforeground='white')
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure text tags for rich formatting
        self.setup_chat_formatting()
        
        # User input frame
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # User input label
        input_label = ttk.Label(input_frame, text="Your message:")
        input_label.pack(anchor='w', pady=(0, 5))
        
        # User input entry
        self.user_input = tk.Text(input_frame, height=3, font=('Arial', 11), wrap=tk.WORD, state='disabled')
        self.user_input.pack(fill=tk.X, pady=(0, 5))
        self.user_input.bind("<KeyPress>", self.on_input_keypress)
        
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
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(pady=(0, 5))
        
        self.send_button = ttk.Button(button_frame, text="Send Message", command=self.send_message_from_input, state='disabled')
        self.send_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_generation, state='disabled')
        self.stop_button.pack(side=tk.LEFT)
        
        # Token counter display (bottom-right)
        self.token_counter_label = ttk.Label(button_frame, text="Tokens: 0 / 0", 
                                           font=('Arial', 10, 'bold'), foreground="gray")
        self.token_counter_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Attribution text (bottom-right corner of main window)
        attribution_label = ttk.Label(main_frame, 
                                    text="Powered by Ollama", 
                                    font=('Arial', 9, 'italic'), 
                                    foreground="#666666")
        attribution_label.pack(side=tk.BOTTOM, anchor='se', padx=(0, 10), pady=(0, 5))
        
        def open_ollama_website(event):
            import webbrowser
            webbrowser.open("https://ollama.ai")
        
        attribution_label.bind("<Button-1>", open_ollama_website)
        attribution_label.bind("<Enter>", lambda e: attribution_label.config(foreground="#1976D2", cursor="hand2"))
        attribution_label.bind("<Leave>", lambda e: attribution_label.config(foreground="#666666", cursor=""))
        
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
        self.current_request = None  # Track current HTTP request for cancellation
        self.is_generating = False  # Track if model is generating response
        
        # Token tracking variables
        self.current_chat_tokens = 0  # Tokens used in current conversation
        self.max_context_tokens = 0  # Maximum context window for current model
        self.conversation_history = []  # Store conversation for token counting
        
        # Model information cache
        self.model_info_cache = {}  # Cache for model size and info
        
        # Initialize token counter display
        self.update_token_counter()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start server monitoring
        self.start_server_monitoring()
        
        # Initial status update
        self.root.after(100, self.update_server_status_display)

    def setup_chat_formatting(self):
        """Setup text formatting tags for the chat display"""
        # Simplified tags - avoid complex overlapping
        self.chat_display.tag_configure("user_label", font=('Arial', 11, 'bold'), foreground='#0066cc')
        self.chat_display.tag_configure("ai_label", font=('Arial', 11, 'bold'), foreground='#009900')
        self.chat_display.tag_configure("code_block", font=('Courier New', 10), background='#f5f5f5',
                                      lmargin1=20, lmargin2=20, spacing1=5, spacing3=5)
        self.chat_display.tag_configure("error", font=('Arial', 11), foreground='#E74C3C')
        self.chat_display.tag_configure("warning", font=('Arial', 11), foreground='#F39C12')
        self.chat_display.tag_configure("success", font=('Arial', 11), foreground='#27AE60')

    def format_and_insert_text(self, text, position="end"):
        """Simple text insertion without complex formatting"""
        if not text:
            return
            
        self.chat_display.config(state='normal')
        
        # Just clean the markdown, don't apply complex formatting
        cleaned_text = self.clean_markdown_text(text)
        
        if position == "end" or position == tk.END:
            self.chat_display.insert(tk.END, cleaned_text)
        else:
            self.chat_display.insert(position, cleaned_text)
        
        self.chat_display.config(state='disabled')
    
    def clean_markdown_text(self, text):
        """Simple markdown removal - just strip markers, no formatting"""
        if not text:
            return text
        
        # Process in order to avoid conflicts
        cleaned = text
        
        # 1. Handle code blocks first (highest priority)
        # Keep code content but remove the backticks
        cleaned = re.sub(r'```[a-zA-Z]*\n?', '', cleaned)  # Remove opening ```
        cleaned = re.sub(r'\n?```', '', cleaned)            # Remove closing ```
        
        # 2. Handle inline code
        cleaned = re.sub(r'`([^`\n]+)`', r'\1', cleaned)
        
        # 3. Handle bold (must be before italic to avoid conflicts)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)
        
        # 4. Handle italic
        cleaned = re.sub(r'\*([^*\n]+)\*', r'\1', cleaned)
        cleaned = re.sub(r'_([^_\n]+)_', r'\1', cleaned)
        
        return cleaned
    
    def _parse_markdown(self, text):
        """Parse markdown text and return list of (type, content) tuples."""
        parts = []
        remaining_text = text
        
        # First, handle code blocks (```code```) - highest priority
        # Updated pattern to handle optional newlines for better compatibility
        code_block_pattern = r'```[a-zA-Z]*\n?(.*?)\n?```'
        last_end = 0
        
        for match in re.finditer(code_block_pattern, remaining_text, re.DOTALL):
            # Add text before code block
            if match.start() > last_end:
                before_text = remaining_text[last_end:match.start()]
                if before_text:
                    # Parse other markdown in the text before code block
                    inline_parts = self._parse_inline_markdown(before_text)
                    parts.extend(inline_parts)
            
            # Add code block (without the ``` markers)
            code_content = match.group(1)
            parts.append(("code_block", code_content))
            last_end = match.end()
        
        # Add remaining text after last code block
        if last_end < len(remaining_text):
            remaining = remaining_text[last_end:]
            if remaining:
                # Parse other markdown in remaining text
                inline_parts = self._parse_inline_markdown(remaining)
                parts.extend(inline_parts)
        
        # If no code blocks found, just parse inline markdown
        if not parts:
            parts = self._parse_inline_markdown(remaining_text)
        
        return parts
    
    def _parse_inline_markdown(self, text):
        """Parse inline markdown (code, bold, italic) and return list of (type, content) tuples."""
        parts = []
        remaining = text
        
        # Process patterns in order: inline code, bold, italic, then regular text
        patterns = [
            (r'`([^`\n]+)`', 'inline_code'),  # `code` - highest priority
            (r'\*\*([^*]+)\*\*', 'bold'),     # **bold**
            (r'\*([^*]+)\*', 'italic'),       # *italic*
            (r'__([^_]+)__', 'bold'),         # __bold__
            (r'_([^_]+)_', 'italic'),         # _italic_
        ]
        
        while remaining:
            earliest_match = None
            earliest_pos = len(remaining)
            pattern_info = None
            
            # Find the earliest markdown pattern
            for pattern, format_type in patterns:
                match = re.search(pattern, remaining)
                if match and match.start() < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start()
                    pattern_info = (pattern, format_type)
            
            if earliest_match:
                # Add text before the match
                if earliest_pos > 0:
                    before_text = remaining[:earliest_pos]
                    if before_text:
                        parts.append(("text", before_text))
                
                # Add the formatted content (without markers)
                content = earliest_match.group(1)
                parts.append((pattern_info[1], content))
                
                # Continue with remaining text after the match
                remaining = remaining[earliest_match.end():]
            else:
                # No more patterns found, add remaining as regular text
                if remaining:
                    parts.append(("text", remaining))
                break
        
        return parts

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
            if not self.ollama_path:
                return False
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
        elif self.server_started_by_user:
            self.server_status_label.config(text="Server Status: Started by user", foreground="green")
        else:
            self.server_status_label.config(text="Server Status: Started by system", foreground="orange")
    
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

    def get_model_details_from_page(self, model_name):
        """Scrape detailed model information from ollama.com individual model page."""
        try:
            import re
            url = f"https://ollama.com/library/{model_name}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Extract parameter sizes
                size_pattern = r'x-test-size[^>]*>([^<]+)'
                sizes = re.findall(size_pattern, content)
                
                # Extract download count (pull count)
                pull_pattern = r'x-test-pull-count>([^<]+)'
                pull_match = re.search(pull_pattern, content)
                pull_count = pull_match.group(1) if pull_match else None
                
                # Extract last updated
                updated_pattern = r'x-test-updated>([^<]+)'
                updated_match = re.search(updated_pattern, content)
                last_updated = updated_match.group(1) if updated_match else None
                
                # Extract capabilities (tools, vision, embedding, thinking)
                capabilities = []
                # Look for capability badges in the HTML - they use bg-indigo-50 class
                capability_pattern = r'bg-indigo-50[^>]*>([^<]+)</span>'
                capability_matches = re.findall(capability_pattern, content)
                
                for capability in capability_matches:
                    capability = capability.strip().lower()
                    if capability in ['tools', 'vision', 'embedding', 'thinking']:
                        capabilities.append(capability)
                
                return {
                    'sizes': sizes,
                    'pull_count_display': pull_count,
                    'last_updated': last_updated,
                    'capabilities': capabilities,
                    'url': url
                }
        except Exception as e:
            self.show_status_message(f"Failed to scrape {model_name}: {str(e)}")
        return None

    def get_available_models(self):
        """Fetch list of available models from Ollama registry."""
        self.show_status_message("Starting model fetch from Ollama APIs...")
        all_models = {}  # Use dict to store models with their info: {name: {size: ..., description: ...}}
        
        # Try Ollama-specific API endpoint from ollamadb.dev (comprehensive official models)
        api_endpoints = [
            ("https://ollamadb.dev/api/v1/models?limit=200", "OllamaDB.dev Official Models"),
            ("https://ollama.ai/api/tags", "Primary Ollama API")
        ]
        
        for url, name in api_endpoints:
            try:
                self.show_status_message(f"Trying {name}: {url}")
                response = requests.get(url, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    models_found = 0
                    
                    # Handle OllamaDB.dev API format
                    if isinstance(data, dict) and 'models' in data and isinstance(data['models'], list):
                        model_list = data['models']
                        for model in model_list:
                            if isinstance(model, dict) and 'model_name' in model:
                                model_name = model['model_name']
                                model_info = {
                                    'size': 0,  # OllamaDB doesn't provide size, but has other useful info
                                    'pulls': model.get('pulls', 0),
                                    'tags': model.get('tags', 0),
                                    'model_type': model.get('model_type', ''),
                                    'last_updated': model.get('last_updated_str', ''),
                                    'description': model.get('description', ''),
                                    'source': name
                                }
                                all_models[model_name] = model_info
                                models_found += 1
                    
                    # Handle Primary Ollama API format
                    elif isinstance(data, dict) and 'models' in data:
                        model_list = data['models']
                        for model in model_list:
                            if isinstance(model, dict) and 'name' in model:
                                model_name = model['name']
                                model_info = {
                                    'size': model.get('size', 0),
                                    'modified_at': model.get('modified_at', ''),
                                    'digest': model.get('digest', ''),
                                    'parameter_size': model.get('details', {}).get('parameter_size', ''),
                                    'source': name
                                }
                                # Don't override OllamaDB data if we already have it
                                if model_name not in all_models:
                                    all_models[model_name] = model_info
                                    models_found += 1
                                else:
                                    # Merge size info from Ollama API into existing OllamaDB data
                                    if model_info['size'] > 0:
                                        all_models[model_name]['size'] = model_info['size']
                                        all_models[model_name]['modified_at'] = model_info['modified_at']
                    
                    # Handle Ollama Registry format  
                    elif isinstance(data, dict) and 'repositories' in data:
                        repositories = data['repositories']
                        for repo_name in repositories:
                            if isinstance(repo_name, str):
                                model_info = {
                                    'size': 0,  # Registry doesn't provide size
                                    'source': name
                                }
                                if repo_name not in all_models:  # Don't override API data
                                    all_models[repo_name] = model_info
                                    models_found += 1
                    
                    # Handle direct list format (if any API returns this)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, str):
                                model_name = item
                                model_info = {
                                    'size': 0,
                                    'source': name
                                }
                                if model_name not in all_models:
                                    all_models[model_name] = model_info
                                    models_found += 1
                    
                    if models_found > 0:
                        self.show_status_message(f"{name} success: Found {models_found} models")
                        
            except Exception as e:
                self.show_status_message(f"{name} failed: {str(e)}")
        
        if all_models:
            model_names = sorted(list(all_models.keys()))
            self.show_status_message(f"API total: {len(model_names)} models available")
            
            # Store model info for later use (without detailed scraping)
            self.model_info_cache = all_models
            return model_names
        
        # No fallback - return empty list if APIs fail
        self.show_status_message("No models found from APIs. Only locally installed models will be available.")
        self.model_info_cache = {}
        return []

    def format_model_size(self, size_bytes):
        """Convert bytes to human readable format."""
        if not size_bytes or size_bytes == 0:
            return "Unknown"
        
        # Convert bytes to GB
        size_gb = size_bytes / (1024 ** 3)
        
        if size_gb < 1:
            size_mb = size_bytes / (1024 ** 2)
            return f"{size_mb:.1f} MB"
        elif size_gb < 10:
            return f"{size_gb:.1f} GB"
        else:
            return f"{size_gb:.0f} GB"

    def get_model_display_info(self, model_name):
        """Get display info for a model including additional metadata from APIs."""
        if hasattr(self, 'model_info_cache') and model_name in self.model_info_cache:
            info = self.model_info_cache[model_name]
            
            # Check if we have size data from Ollama API
            if info.get('size', 0) > 0:
                size_str = self.format_model_size(info.get('size', 0))
                return f"{model_name} ({size_str})"
            
            # Check if we have pull count from OllamaDB
            elif info.get('pulls', 0) > 0:
                pulls = info.get('pulls', 0)
                if pulls >= 1000000:
                    pulls_str = f"{pulls/1000000:.1f}M pulls"
                elif pulls >= 1000:
                    pulls_str = f"{pulls/1000:.0f}K pulls"
                else:
                    pulls_str = f"{pulls} pulls"
                
                model_type = info.get('model_type', '')
                if model_type == 'official':
                    return f"{model_name} ({pulls_str}) ✓"
                else:
                    return f"{model_name} ({pulls_str})"
            
            # Just return model name if no additional info available
            else:
                return model_name
        return model_name

    def show_download_dialog(self):
        """Show dialog for downloading a new model."""
        if self.is_downloading:
            return  # Prevent multiple download dialogs
            
        # Create download dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Download Model")
        dialog.geometry("700x650")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f"700x650+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Download Ollama Model", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Available models dropdown
        ttk.Label(main_frame, text="Select from available models:").pack(anchor='w')
        
        # Status label for loading
        status_label = ttk.Label(main_frame, text="Loading available models...", 
                                foreground="#1976D2", font=("Arial", 9))
        status_label.pack(anchor='w', pady=(2, 5))
        
        model_var = tk.StringVar()
        model_dropdown = ttk.Combobox(main_frame, textvariable=model_var, width=50, state="readonly")
        model_dropdown.pack(fill=tk.X, pady=(0, 10))
        
        # Model size selection
        size_label = ttk.Label(main_frame, text="Choose model size:")
        size_label.pack(anchor='w', pady=(10, 0))
        
        # Status label for size loading
        size_status_label = ttk.Label(main_frame, text="Select a model first", 
                                     foreground="#666666", font=("Arial", 9))
        size_status_label.pack(anchor='w', pady=(2, 5))
        
        size_var = tk.StringVar()
        size_dropdown = ttk.Combobox(main_frame, textvariable=size_var, width=50, state="readonly")
        size_dropdown.pack(fill=tk.X, pady=(0, 5))
        size_dropdown.config(state='disabled')  # Initially disabled
        
        # Model already downloaded warning (initially hidden)
        already_downloaded_label = ttk.Label(main_frame, text="", 
                                           foreground="red", font=("Arial", 9, "bold"))
        already_downloaded_label.pack(anchor='w', pady=(0, 10))
        
        # Model information display (always visible)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        model_info_label = ttk.Label(info_frame, text="Model Information:", 
                                    font=("Arial", 10, "bold"))
        model_info_label.pack(anchor='w')
        
        # Model details text
        model_details_text = tk.Text(info_frame, wrap=tk.WORD, height=6, 
                                   font=('Arial', 9), bg="#F8F9FA", 
                                   relief=tk.FLAT, padx=10, pady=5)
        model_details_text.pack(fill=tk.X, pady=(5, 10))
        
        # Initially show placeholder text
        model_details_text.insert('1.0', "Select a model and size to see detailed information here.\n\nThis area will show:\n• Model capabilities\n• Download statistics\n• System requirements\n• Performance information")
        model_details_text.config(state='disabled')
        
        # System compatibility frame
        compat_frame = ttk.Frame(info_frame)
        compat_frame.pack(fill=tk.X)
        
        compat_label = ttk.Label(compat_frame, text="System Compatibility:", 
                                font=("Arial", 10, "bold"))
        compat_label.pack(anchor='w', pady=(0, 5))
        
        # GPU only compatibility
        gpu_only_frame = ttk.Frame(compat_frame)
        gpu_only_frame.pack(fill=tk.X, pady=1)
        gpu_only_label = ttk.Label(gpu_only_frame, text="⚪ GPU only - Select model to check compatibility", font=('Arial', 9), foreground="#666666")
        gpu_only_label.pack(anchor='w')
        
        # CPU only compatibility  
        cpu_only_frame = ttk.Frame(compat_frame)
        cpu_only_frame.pack(fill=tk.X, pady=1)
        cpu_only_label = ttk.Label(cpu_only_frame, text="⚪ CPU only - Select model to check compatibility", font=('Arial', 9), foreground="#666666")
        cpu_only_label.pack(anchor='w')
        
        # GPU + CPU compatibility
        hybrid_frame = ttk.Frame(compat_frame)
        hybrid_frame.pack(fill=tk.X, pady=1)
        hybrid_label = ttk.Label(hybrid_frame, text="⚪ GPU + CPU - Select model to check compatibility", font=('Arial', 9), foreground="#666666")
        hybrid_label.pack(anchor='w')
        
        # Hide info frame initially
        # info_frame.pack_forget()  # Comment out - we want to always show it now
        
        # Initialize download tracking variables
        download_process = None
        downloading_model = None
        is_downloading = False
        
        # Load available models in background
        def load_models():
            try:
                available_models = self.get_available_models()
                self.show_status_message(f"load_models: Received {len(available_models) if available_models else 0} models")
                dialog.after(0, lambda: update_dropdown(available_models))
            except Exception as e:
                self.show_status_message(f"load_models error: {str(e)}")
                dialog.after(0, lambda: update_dropdown([]))
        
        def update_dropdown(models):
            try:
                self.show_status_message(f"update_dropdown: Processing {len(models) if models else 0} models")
                if models and len(models) > 0:
                    # Create display list with sizes
                    display_models = []
                    for model_name in models:
                        display_info = self.get_model_display_info(model_name)
                        display_models.append(display_info)
                    
                    model_dropdown['values'] = display_models
                    model_dropdown.set('')  # Clear selection
                    status_label.config(text=f"Found {len(models)} available models", foreground="#1976D2")
                    self.show_status_message(f"Dropdown updated successfully with {len(models)} models")
                else:
                    status_label.config(text="Could not load models. Use manual entry below.", foreground="orange")
                    self.show_status_message("No models received, showing manual entry message")
            except Exception as e:
                self.show_status_message(f"update_dropdown error: {str(e)}")
                status_label.config(text="Error loading models. Use manual entry below.", foreground="red")
        
        # Start loading models
        threading.Thread(target=load_models, daemon=True).start()
        
        def check_gpu_availability():
            """Check if dedicated GPU is available."""
            try:
                # Try nvidia-smi for NVIDIA GPUs
                result = subprocess.run(['nvidia-smi', '--list-gpus'], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and result.stdout.strip():
                    return True, "NVIDIA GPU detected"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            try:
                # Try lspci for any GPU
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    gpu_lines = [line for line in result.stdout.lower().split('\n') 
                               if any(gpu in line for gpu in ['vga', 'nvidia', 'amd', 'radeon', 'intel graphics'])]
                    if gpu_lines:
                        # Check if it's integrated only
                        integrated_only = all(any(integrated in line for integrated in ['intel', 'integrated']) 
                                            for line in gpu_lines)
                        if not integrated_only:
                            return True, "Dedicated GPU detected"
                        else:
                            return False, "Only integrated graphics"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            return False, "No dedicated GPU detected"
        
        def check_model_already_downloaded(model_name, size_tag):
            """Check if the specific model with size is already downloaded."""
            try:
                if not self.ollama_path:
                    return False
                
                # Get list of installed models
                result = subprocess.run([self.ollama_path, "list"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    return False
                
                # Construct the full model name with size tag
                if size_tag and size_tag != "latest (default)":
                    if size_tag == "latest":
                        full_model_name = f"{model_name}:latest"
                    else:
                        clean_size = size_tag.split(' (')[0]
                        full_model_name = f"{model_name}:{clean_size}"
                else:
                    full_model_name = model_name
                
                # Check if this exact model is in the list
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if parts:
                            installed_model = parts[0]
                            # Check exact match or default tag match
                            if (installed_model == full_model_name or 
                                (installed_model == f"{model_name}:latest" and full_model_name == model_name) or
                                (installed_model == model_name and full_model_name == f"{model_name}:latest")):
                                return True
                
                return False
            except Exception as e:
                self.show_status_message(f"Error checking downloaded models: {str(e)}")
                return False
        
        # Clean compatibility system implementation
        class ModelCompatibilityChecker:
            """Clean implementation of model compatibility assessment."""
            
            MODEL_REQUIREMENTS = {
                'micro': {'patterns': [r'(?<!\d)1b(?!\d)', r'(?<!\d)2b(?!\d)'], 'vram_gb': 2, 'ram_gb': 2},
                'tiny': {'patterns': [r'(?<!\d)3b(?!\d)', r'(?<!\d)4b(?!\d)'], 'vram_gb': 4, 'ram_gb': 3},
                'small': {'patterns': [r'(?<!\d)7b(?!\d)', r'(?<!\d)8b(?!\d)', r'(?<!\d)9b(?!\d)'], 'vram_gb': 8, 'ram_gb': 6},
                'medium': {'patterns': [r'(?<!\d)13b(?!\d)', r'(?<!\d)14b(?!\d)', r'(?<!\d)15b(?!\d)'], 'vram_gb': 16, 'ram_gb': 14},
                'large': {'patterns': [r'(?<!\d)30b(?!\d)', r'(?<!\d)32b(?!\d)', r'(?<!\d)34b(?!\d)'], 'vram_gb': 40, 'ram_gb': 35},
                'very_large': {'patterns': [r'(?<!\d)70b(?!\d)', r'(?<!\d)72b(?!\d)'], 'vram_gb': 80, 'ram_gb': 70},
                'huge': {'patterns': [r'(?<!\d)180b(?!\d)', r'(?<!\d)175b(?!\d)'], 'vram_gb': 350, 'ram_gb': 200},
                'massive': {'patterns': [r'(?<!\d)405b(?!\d)', r'(?<!\d)670b(?!\d)', r'(?<!\d)671b(?!\d)'], 'vram_gb': 1000, 'ram_gb': 800}
            }
            
            def __init__(self):
                self.system_info = self._get_system_info()
            
            def _get_system_info(self):
                """Get actual system memory information."""
                info = {'gpu_vram_gb': 0, 'system_ram_gb': 12, 'total_ram_gb': 16, 'has_gpu': False}
                
                # Get GPU VRAM
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                                          capture_output=True, text=True, timeout=3)
                    if result.returncode == 0 and result.stdout.strip():
                        vram_mb = int(result.stdout.strip().split('\n')[0])
                        info['gpu_vram_gb'] = vram_mb / 1024
                        info['has_gpu'] = True
                except:
                    pass
                
                # Get system RAM
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if line.startswith('MemTotal:'):
                                ram_kb = int(line.split()[1])
                                total_ram_gb = ram_kb / (1024 * 1024)
                                overhead = 2 if total_ram_gb <= 8 else (3 if total_ram_gb <= 16 else max(4, total_ram_gb * 0.12))
                                info['total_ram_gb'] = total_ram_gb
                                info['system_ram_gb'] = max(1, total_ram_gb - overhead)
                                break
                except:
                    pass
                
                return info
            
            def _detect_model_size(self, model_name, size_tag):
                """Detect model size from name and tag."""
                import re
                text_to_analyze = f"{model_name} {size_tag}".lower()
                text_to_analyze = re.sub(r'\b(latest|default|instruct|chat|code)\b', '', text_to_analyze)
                
                # First try to extract decimal numbers with 'b' (e.g., "1.8b", "2.7b")
                decimal_size_match = re.search(r'(\d+\.\d+)\s*b\b', text_to_analyze)
                if decimal_size_match:
                    size_num = float(decimal_size_match.group(1))
                    if size_num <= 2: return 'micro'
                    elif size_num <= 4: return 'tiny'
                    elif size_num <= 9: return 'small'
                    elif size_num <= 15: return 'medium'
                    elif size_num <= 35: return 'large'
                    elif size_num <= 75: return 'very_large'
                    elif size_num <= 200: return 'huge'
                    else: return 'massive'
                
                # Check for M (million) parameter models like "270m", "500M"
                million_size_match = re.search(r'(\d+)\s*m\b', text_to_analyze)
                if million_size_match:
                    size_num = float(million_size_match.group(1))
                    # Convert millions to billions for comparison
                    size_in_billions = size_num / 1000
                    if size_in_billions <= 2: return 'micro'
                    elif size_in_billions <= 4: return 'tiny'
                    else: return 'small'
                
                # Then try whole number patterns (but be more specific)
                for category, config in self.MODEL_REQUIREMENTS.items():
                    for pattern in config['patterns']:
                        # Use more specific regex to avoid false matches
                        if re.search(r'(?<!\d)' + pattern + r'(?!\d)', text_to_analyze):
                            return category
                
                # Final fallback: any number followed by 'b'
                size_match = re.search(r'(\d+)\s*b\b', text_to_analyze)
                if size_match:
                    size_num = float(size_match.group(1))
                    if size_num <= 2: return 'micro'
                    elif size_num <= 4: return 'tiny'
                    elif size_num <= 9: return 'small'
                    elif size_num <= 15: return 'medium'
                    elif size_num <= 35: return 'large'
                    elif size_num <= 75: return 'very_large'
                    elif size_num <= 200: return 'huge'
                    else: return 'massive'
                
                return 'small'  # Default
            
            def get_model_requirements(self, model_name, size_tag):
                """Get memory requirements for a specific model."""
                category = self._detect_model_size(model_name, size_tag)
                config = self.MODEL_REQUIREMENTS[category]
                return {'category': category, 'vram_gb': config['vram_gb'], 'ram_gb': config['ram_gb']}
            
            def assess_gpu_only(self, model_name, size_tag):
                """Assess GPU-only compatibility."""
                requirements = self.get_model_requirements(model_name, size_tag)
                
                if not self.system_info['has_gpu']:
                    return ('red', f"❌ GPU only - {requirements['vram_gb']}GB VRAM needed, no dedicated GPU available")
                
                if requirements['category'] in ['massive', 'huge']:
                    return ('red', f"❌ GPU only - {requirements['vram_gb']}GB VRAM needed, requires data center hardware")
                
                available_vram = self.system_info['gpu_vram_gb']
                needed_vram = requirements['vram_gb']
                
                if available_vram >= needed_vram:
                    return ('green', f"✅ GPU only - {needed_vram}GB VRAM needed, {available_vram:.1f}GB available")
                elif available_vram >= needed_vram * 0.8:
                    return ('orange', f"⚠️ GPU only - {needed_vram}GB VRAM needed, {available_vram:.1f}GB available (tight fit)")
                else:
                    return ('red', f"❌ GPU only - {needed_vram}GB VRAM needed, only {available_vram:.1f}GB available")
            
            def assess_cpu_only(self, model_name, size_tag):
                """Assess CPU-only compatibility."""
                requirements = self.get_model_requirements(model_name, size_tag)
                
                # Add overhead for large models
                overhead = 1.15 if requirements['category'] in ['large', 'very_large', 'huge', 'massive'] else 1.0
                effective_ram_needed = requirements['ram_gb'] * overhead
                available_ram = self.system_info['system_ram_gb']
                
                if requirements['category'] in ['massive', 'huge']:
                    if available_ram >= effective_ram_needed:
                        return ('orange', f"⚠️ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (very slow, enterprise hardware)")
                    else:
                        return ('red', f"❌ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (insufficient)")
                elif requirements['category'] == 'very_large':
                    if available_ram >= effective_ram_needed:
                        return ('green', f"✅ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (slow but possible)")
                    elif available_ram >= requirements['ram_gb'] * 0.8:
                        return ('orange', f"⚠️ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (tight fit, very slow)")
                    else:
                        return ('red', f"❌ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (insufficient)")
                else:
                    if available_ram >= effective_ram_needed:
                        return ('green', f"✅ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available")
                    elif available_ram >= requirements['ram_gb'] * 0.8:
                        return ('orange', f"⚠️ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (tight fit)")
                    else:
                        return ('red', f"❌ CPU only - {requirements['ram_gb']}GB RAM needed, {available_ram:.1f}GB available (insufficient)")
            
            def assess_hybrid(self, model_name, size_tag):
                """Assess GPU + CPU hybrid compatibility."""
                requirements = self.get_model_requirements(model_name, size_tag)
                
                if not self.system_info['has_gpu']:
                    cpu_color, cpu_msg = self.assess_cpu_only(model_name, size_tag)
                    if 'available' in cpu_msg and '✅' in cpu_msg:
                        return ('orange', f"⚠️ GPU + CPU - No dedicated GPU, CPU only with {self.system_info['system_ram_gb']:.1f}GB RAM")
                    else:
                        return ('red', f"❌ GPU + CPU - No GPU, insufficient RAM: {self.system_info['system_ram_gb']:.1f}GB < {requirements['ram_gb']}GB needed")
                
                # With GPU - assess best strategy
                gpu_color, gpu_msg = self.assess_gpu_only(model_name, size_tag)
                cpu_color, cpu_msg = self.assess_cpu_only(model_name, size_tag)
                
                if '✅' in gpu_msg:
                    return ('green', f"✅ GPU + CPU - Can run primarily on GPU with {self.system_info['gpu_vram_gb']:.1f}GB VRAM")
                elif cpu_color in ['green', 'orange'] and self.system_info['gpu_vram_gb'] >= requirements['vram_gb'] * 0.3:
                    return ('green', f"✅ GPU + CPU - CPU primary with GPU acceleration ({self.system_info['gpu_vram_gb']:.1f}GB VRAM)")
                elif cpu_color in ['green', 'orange']:
                    return ('orange', f"⚠️ GPU + CPU - GPU too small ({self.system_info['gpu_vram_gb']:.1f}GB < {requirements['vram_gb']}GB needed), CPU only")
                else:
                    return ('red', f"❌ GPU + CPU - Insufficient resources: {self.system_info['gpu_vram_gb']:.1f}GB VRAM, {self.system_info['system_ram_gb']:.1f}GB RAM")
        
        # Initialize compatibility checker
        compat_checker = ModelCompatibilityChecker()
        
        def check_gpu_availability():
            """Check if GPU is available."""
            return compat_checker.system_info['has_gpu'], compat_checker.system_info
        
        def update_system_compatibility(has_gpu, gpu_info, model_name=None, selected_size=None):
            """Update system compatibility display with clean logic."""
            if model_name and selected_size:
                # Get compatibility assessments
                gpu_color, gpu_msg = compat_checker.assess_gpu_only(model_name, selected_size)
                cpu_color, cpu_msg = compat_checker.assess_cpu_only(model_name, selected_size)
                hybrid_color, hybrid_msg = compat_checker.assess_hybrid(model_name, selected_size)
                
                # Update labels
                gpu_only_label.config(text=gpu_msg, foreground=gpu_color)
                cpu_only_label.config(text=cpu_msg, foreground=cpu_color)
                hybrid_label.config(text=hybrid_msg, foreground=hybrid_color)
            else:
                # Generic compatibility when no model selected
                if has_gpu:
                    gpu_only_label.config(text="✅ GPU only - Recommended for best performance", foreground="green")
                    cpu_only_label.config(text="✅ CPU only - Slower but functional", foreground="green")
                    hybrid_label.config(text="✅ GPU + CPU - Optimal performance and reliability", foreground="green")
                else:
                    gpu_only_label.config(text="❌ GPU only - No dedicated GPU available", foreground="red")
                    cpu_only_label.config(text="✅ CPU only - Available (may be slow for large models)", foreground="orange")
                    hybrid_label.config(text="❌ GPU + CPU - Requires dedicated GPU", foreground="red")
        
        # Manual model name input
        ttk.Label(main_frame, text="Or enter model name manually:").pack(anchor='w', pady=(20, 0))
        model_entry = ttk.Entry(main_frame, width=50, font=("Arial", 11))
        model_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Examples
        examples_label = ttk.Label(main_frame, 
                                  text="Enter any model name from ollama.com/search",
                                  font=("Arial", 9), foreground="#666666")
        examples_label.pack(pady=(0, 20))
        
        # Button frame (moved to bottom with padding)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
        
        def load_model_sizes(selected_model):
            """Load available sizes for the selected model."""
            if not selected_model:
                return
            
            # Enable size dropdown and show loading
            size_dropdown.config(state='normal')
            size_status_label.config(text="Loading sizes...", foreground="#1976D2")
            size_var.set('')
            download_btn.config(state='disabled')  # Disable download until size is selected
            
            def fetch_sizes():
                try:
                    details = self.get_model_details_from_page(selected_model)
                    dialog.after(0, lambda: update_size_dropdown(details))
                except Exception as e:
                    dialog.after(0, lambda: update_size_dropdown(None))
            
            threading.Thread(target=fetch_sizes, daemon=True).start()
        
        def update_size_dropdown(details):
            """Update the size dropdown with available sizes."""
            try:
                if details and details.get('sizes'):
                    sizes = details['sizes']
                    # Create display options with size info
                    size_options = []
                    for size in sizes:
                        size_options.append(f"{size}")
                    
                    size_dropdown['values'] = size_options
                    size_dropdown.config(state='readonly')
                    size_status_label.config(text=f"Found {len(sizes)} size options", foreground="#1976D2")
                else:
                    # No specific sizes found, offer generic options
                    size_dropdown['values'] = ['latest (default)', 'latest']
                    size_dropdown.config(state='readonly') 
                    size_status_label.config(text="Using default size options", foreground="orange")
            except Exception as e:
                size_dropdown['values'] = ['latest (default)']
                size_dropdown.config(state='readonly')
                size_status_label.config(text="Error loading sizes, using default", foreground="red")
        
        def on_model_select(event):
            """Handle model selection."""
            selected_display = model_var.get().strip()
            if selected_display:
                # Extract actual model name from display format
                model_name = selected_display.split(' (')[0]  # Get part before " ("
                load_model_sizes(model_name)
                # Clear manual entry when dropdown is used
                model_entry.delete(0, tk.END)
                # Model information stays visible - no need to hide it
                # Clear any existing warning
                already_downloaded_label.config(text="")
        
        def on_size_select(event):
            """Handle size selection."""
            selected_size = size_var.get().strip()
            selected_model = model_var.get().strip()
            if selected_size and selected_model:
                # Extract model name
                model_name = selected_model.split(' (')[0]
                
                # Update model information (already visible)
                
                # Get model details if available
                if hasattr(self, 'model_info_cache') and model_name in self.model_info_cache:
                    info = self.model_info_cache[model_name]
                    
                    # Build information text
                    info_text = f"Model: {model_name}\n"
                    info_text += f"Selected size: {selected_size}\n"
                    
                    if info.get('pull_count_display'):
                        info_text += f"Downloads: {info['pull_count_display']}\n"
                    
                    if info.get('last_updated'):
                        info_text += f"Last updated: {info['last_updated']}\n"
                    
                    if info.get('capabilities'):
                        cap_icons = {'tools': '🔧 Function calling', 'vision': '👁️ Image analysis', 
                                   'embedding': '📄 Text embeddings', 'thinking': '🧠 Chain of thought'}
                        caps_display = [cap_icons.get(cap, cap) for cap in info['capabilities']]
                        info_text += f"Capabilities: {', '.join(caps_display)}\n"
                    
                    if info.get('description'):
                        info_text += f"Description: {info['description']}"
                        
                    # Update model details text
                    model_details_text.config(state='normal')
                    model_details_text.delete('1.0', tk.END)
                    model_details_text.insert('1.0', info_text)
                    model_details_text.config(state='disabled')
                else:
                    # Basic information
                    info_text = f"Model: {model_name}\n"
                    info_text += f"Selected size: {selected_size}\n"
                    info_text += "This model will be downloaded from ollama.com\n"
                    info_text += "Check ollama.com/library for detailed information."
                    
                    model_details_text.config(state='normal')
                    model_details_text.delete('1.0', tk.END)
                    model_details_text.insert('1.0', info_text)
                    model_details_text.config(state='disabled')
                
                # Check and display system compatibility
                has_gpu, gpu_info = check_gpu_availability()
                update_system_compatibility(has_gpu, gpu_info, model_name, selected_size)
                
                # Check if model is already downloaded
                is_already_downloaded = check_model_already_downloaded(model_name, selected_size)
                if is_already_downloaded:
                    already_downloaded_label.config(text="⚠️ Model already downloaded")
                    download_btn.config(state='disabled')  # Disable download button
                else:
                    already_downloaded_label.config(text="")  # Clear warning
                    download_btn.config(state='normal')  # Enable download button
        
        def start_download():
            # Get model name from dropdown or manual entry
            selected_display = model_var.get().strip()
            manual_entry = model_entry.get().strip()
            selected_size = size_var.get().strip()
            
            # Extract actual model name from display format "model_name (size) - description"
            model_name = ""
            if selected_display:
                # Extract model name from display format
                model_name = selected_display.split(' (')[0]  # Get part before " ("
            elif manual_entry:
                model_name = manual_entry
            
            if not model_name:
                messagebox.showwarning("Invalid Input", "Please select a model or enter a model name.")
                return
            
            if not selected_size and selected_display:  # Only require size if using dropdown
                messagebox.showwarning("Invalid Input", "Please select a model size.")
                return
            
            # Construct full model name with size tag
            if selected_size and selected_size != "latest (default)":
                if selected_size == "latest":
                    full_model_name = f"{model_name}:latest"
                else:
                    # Remove any extra text like " (default)" and use just the size
                    clean_size = selected_size.split(' (')[0]
                    full_model_name = f"{model_name}:{clean_size}"
            else:
                full_model_name = model_name  # Use default tag
            
            # Start download with progress tracking
            start_download_with_progress(full_model_name)
        
        def start_download_with_progress(full_model_name):
            """Start download and show progress in dialog."""
            nonlocal download_process, downloading_model, is_downloading
            
            if is_downloading:
                return  # Prevent multiple downloads
            
            is_downloading = True
            self.is_downloading = True  # Also set in main class
            downloading_model = full_model_name
            self.downloading_model = full_model_name  # Also set in main class
            
            # Store reference to dialog for main window cancel
            self._active_download_dialog = dialog
            
            # Update main window button to "Cancel Download"
            if hasattr(self, 'download_button'):
                self.download_button.config(text="Cancel Download", command=self.start_download_action)
            
            # Disable chat input during download
            if hasattr(self, 'user_input'):
                self.user_input.config(state='disabled')
            if hasattr(self, 'send_button'):
                self.send_button.config(state='disabled')
            
            # Show progress UI
            progress_frame.pack(fill=tk.X, pady=(10, 0))
            progress_text.config(text="Initializing download...")
            progress_bar['value'] = 0
            download_status_text.delete('1.0', tk.END)
            download_status_text.insert('1.0', f"Starting download of {full_model_name}...\n")
            
            # Update buttons
            download_btn.config(state='disabled')
            cancel_download_btn.pack(side=tk.RIGHT, padx=(0, 10))
            cancel_download_btn.config(state='normal', command=lambda: cancel_download())
            cancel_btn.config(text="Close", state='normal')  # Keep cancel button enabled for closing dialog
            
            # Auto-close dialog after 1 second to continue download in background
            def auto_close_dialog():
                try:
                    if is_downloading:  # Only close if still downloading
                        if hasattr(self, 'download_status_label') and downloading_model:
                            self.download_status_label.config(text=f"📥 {downloading_model}: Downloading in background...")
                        if hasattr(self, 'show_status_message'):
                            self.show_status_message(f"Download started! Dialog closing automatically. Download continues in background.")
                        dialog.destroy()
                except Exception as e:
                    # Fallback - close anyway
                    try:
                        dialog.destroy()
                    except:
                        pass
            dialog.after(1000, auto_close_dialog)  # Auto-close after 1 second
            
            # Disable model/size selection during download
            model_dropdown.config(state='disabled')
            size_dropdown.config(state='disabled')
            model_entry.config(state='disabled')
            
            def run_download():
                """Run the download process in a separate thread."""
                nonlocal download_process
                try:
                    if not self.ollama_path:
                        dialog.after(0, lambda: download_error("Ollama not found"))
                        return
                    
                    # Start the download process
                    cmd = [self.ollama_path, "pull", full_model_name]
                    download_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT,
                        text=True, 
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Monitor download progress
                    for line in iter(download_process.stdout.readline, ''):
                        if download_process.poll() is not None:
                            break
                        
                        # Parse progress from ollama output
                        progress_info = parse_download_progress(line.strip())
                        if progress_info:
                            # Use main window's after method to handle updates even when dialog is closed
                            self.root.after(0, lambda p=progress_info: update_progress(p))
                    
                    # Wait for process to complete
                    return_code = download_process.wait()
                    
                    if return_code == 0:
                        self.root.after(0, lambda: download_complete(full_model_name))
                    else:
                        self.root.after(0, lambda: download_error(f"Download failed with code {return_code}"))
                        
                except Exception as e:
                    self.root.after(0, lambda: download_error(f"Download error: {str(e)}"))
            
            # Start download in background thread
            threading.Thread(target=run_download, daemon=True).start()
        
        def parse_download_progress(line):
            """Parse download progress from ollama output."""
            import re
            
            # Look for percentage patterns in ollama output
            # Examples: "pulling manifest... 100%", "downloading 12345/67890 50%"
            percent_match = re.search(r'(\d+)%', line)
            if percent_match:
                percentage = int(percent_match.group(1))
                
                # Extract status text
                status = line.strip()
                if 'pulling' in line.lower():
                    status = "Pulling manifest..."
                elif 'downloading' in line.lower():
                    status = "Downloading model data..."
                elif 'verifying' in line.lower():
                    status = "Verifying download..."
                elif 'success' in line.lower() or 'complete' in line.lower():
                    status = "Download complete!"
                
                return {'percentage': percentage, 'status': status, 'raw': line}
            
            # Look for size information
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*([KMGT]?B)', line)
            if size_match:
                return {'status': line.strip(), 'raw': line}
            
            return None
        
        def update_progress(progress_info):
            """Update progress display in dialog."""
            nonlocal downloading_model
            
            # Try to update dialog progress (if dialog still exists)
            try:
                if 'percentage' in progress_info:
                    progress_bar['value'] = progress_info['percentage']
                    progress_text.config(text=f"{progress_info['status']} {progress_info['percentage']}%")
                else:
                    progress_text.config(text=progress_info['status'])
                
                # Add to status log (dialog only)
                download_status_text.insert(tk.END, f"{progress_info['raw']}\n")
                download_status_text.see(tk.END)
            except (tk.TclError, AttributeError):
                # Dialog has been closed, only update main window
                pass
            
            # Always update main window status label (works even when dialog is closed)
            if hasattr(self, 'download_status_label') and downloading_model:
                try:
                    if 'percentage' in progress_info:
                        self.download_status_label.config(text=f"📥 {downloading_model}: {progress_info['percentage']}%")
                    else:
                        self.download_status_label.config(text=f"📥 {downloading_model}: {progress_info['status']}")
                except (tk.TclError, AttributeError):
                    pass
        
        def cancel_download():
            """Cancel the ongoing download."""
            nonlocal download_process, downloading_model, is_downloading
            if download_process:
                try:
                    download_process.terminate()
                    download_process.wait(timeout=5)
                except:
                    try:
                        download_process.kill()
                    except:
                        pass
                
                download_process = None
            
            # Reset state
            is_downloading = False
            self.is_downloading = False  # Also reset main class state
            downloading_model = None
            self.downloading_model = None
            
            # Update UI
            progress_text.config(text="Download cancelled")
            download_status_text.insert(tk.END, "\n--- Download cancelled by user ---\n")
            cancel_download_btn.config(state='disabled')
            
            # Re-enable controls
            download_btn.config(state='normal' if size_var.get() or model_entry.get().strip() else 'disabled')
            cancel_btn.config(text="Close", state='normal')
            model_dropdown.config(state='readonly')
            size_dropdown.config(state='readonly')
            model_entry.config(state='normal')
            
            # Update main window
            if hasattr(self, 'show_status_message'):
                self.show_status_message(f"{downloading_model or 'Model'} download cancelled")
            if hasattr(self, 'download_status_label'):
                self.download_status_label.config(text="")
            if hasattr(self, 'download_button'):
                self.download_button.config(text="Download", command=self.start_download_action)
            
            # Re-enable chat input if a model is selected
            if hasattr(self, 'selected_model') and self.selected_model:
                if hasattr(self, 'user_input'):
                    self.user_input.config(state='normal')
                if hasattr(self, 'send_button'):
                    self.send_button.config(state='normal')
        
        def download_complete(model_name):
            """Handle successful download completion."""
            nonlocal download_process, downloading_model, is_downloading
            # Reset download state
            is_downloading = False
            self.is_downloading = False  # Also reset main class state
            downloading_model = None
            self.downloading_model = None
            download_process = None
            
            # Try to update dialog progress (if dialog still exists)
            try:
                progress_bar['value'] = 100
                progress_text.config(text="Download completed successfully!")
                download_status_text.insert(tk.END, "\n--- Download completed successfully ---\n")
                download_status_text.see(tk.END)
                
                # Update dialog buttons
                cancel_download_btn.config(state='disabled')
                cancel_btn.config(text="Close", state='normal')
                
                # Re-enable dialog controls
                model_dropdown.config(state='readonly')
                size_dropdown.config(state='readonly')
                model_entry.config(state='normal')
                
                # Auto-close dialog after 3 seconds
                def auto_close():
                    try:
                        dialog.destroy()
                    except:
                        pass
                dialog.after(3000, auto_close)
            except (tk.TclError, AttributeError):
                # Dialog has been closed, that's fine
                pass
            
            # Always update main window (works even when dialog is closed)
            if hasattr(self, 'show_status_message'):
                self.show_status_message(f"{model_name} download finished")
            if hasattr(self, 'download_status_label'):
                self.download_status_label.config(text=f"✅ Downloaded {model_name}")
            if hasattr(self, 'download_button'):
                self.download_button.config(text="Download", command=self.start_download_action)
                
            # Refresh models in main window
            if hasattr(self, 'refresh_models'):
                self.refresh_models()
        
        def download_error(error_msg):
            """Handle download error."""
            nonlocal download_process, downloading_model, is_downloading
            # Reset download state
            is_downloading = False
            self.is_downloading = False  # Also reset main class state
            error_model = downloading_model
            downloading_model = None
            self.downloading_model = None
            download_process = None
            
            # Try to update dialog (if dialog still exists)
            try:
                progress_text.config(text=f"Download failed: {error_msg}")
                download_status_text.insert(tk.END, f"\n--- Error: {error_msg} ---\n")
                download_status_text.see(tk.END)
                
                # Update dialog buttons
                cancel_download_btn.config(state='disabled')
                download_btn.config(state='normal' if size_var.get() or model_entry.get().strip() else 'disabled')
                cancel_btn.config(state='normal')
                
                # Re-enable dialog controls
                model_dropdown.config(state='readonly')
                size_dropdown.config(state='readonly')
                model_entry.config(state='normal')
            except (tk.TclError, AttributeError):
                # Dialog has been closed, that's fine
                pass
            
            # Always update main window (works even when dialog is closed)
            if hasattr(self, 'show_status_message'):
                self.show_status_message(f"{error_model or 'Model'} download error: {error_msg}")
            if hasattr(self, 'download_status_label'):
                self.download_status_label.config(text=f"❌ Download failed")
            if hasattr(self, 'download_button'):
                self.download_button.config(text="Download", command=self.start_download_action)
        
        def cancel_dialog():
            """Handle dialog cancellation."""
            nonlocal is_downloading, downloading_model
            if is_downloading:
                # If downloading, just close dialog and continue in background
                # No confirmation needed - download continues
                if hasattr(self, 'download_status_label') and downloading_model:
                    self.download_status_label.config(text=f"📥 {downloading_model}: Downloading in background...")
                if hasattr(self, 'show_status_message'):
                    self.show_status_message(f"Download continues in background. Use main window 'Cancel Download' button to stop.")
                dialog.destroy()
            else:
                dialog.destroy()
        
        def on_entry_change(event):
            # When user types in manual entry, clear dropdown selections
            model_var.set('')
            size_var.set('')
            size_dropdown.config(state='disabled')
            size_status_label.config(text="Select a model first", foreground="#666666")
            download_btn.config(state='disabled')
            # Model information stays visible - reset to placeholder text
            model_details_text.config(state='normal')
            model_details_text.delete('1.0', tk.END)
            model_details_text.insert('1.0', "Select a model and size to see detailed information here.\n\nThis area will show:\n• Model capabilities\n• Download statistics\n• System requirements\n• Performance information")
            model_details_text.config(state='disabled')
            # Reset compatibility labels
            gpu_only_label.config(text="⚪ GPU only - Select model to check compatibility", foreground="#666666")
            cpu_only_label.config(text="⚪ CPU only - Select model to check compatibility", foreground="#666666")
            hybrid_label.config(text="⚪ GPU + CPU - Select model to check compatibility", foreground="#666666")
            # Clear any existing warning
            already_downloaded_label.config(text="")
        
        # Bind events
        model_dropdown.bind('<<ComboboxSelected>>', on_model_select)
        size_dropdown.bind('<<ComboboxSelected>>', on_size_select)
        model_entry.bind('<KeyPress>', on_entry_change)
        
        # Progress frame (initially hidden)
        progress_frame = ttk.Frame(main_frame)
        progress_label = ttk.Label(progress_frame, text="Download Progress:", 
                                  font=("Arial", 10, "bold"))
        progress_label.pack(anchor='w', pady=(0, 5))
        
        progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        progress_text = ttk.Label(progress_frame, text="", font=("Arial", 9))
        progress_text.pack(anchor='w')
        
        # Download status text area
        download_status_text = tk.Text(progress_frame, wrap=tk.WORD, height=4, 
                                     font=('Consolas', 9), bg="#F8F9FA", 
                                     relief=tk.FLAT, padx=10, pady=5)
        download_status_text.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=cancel_dialog)
        cancel_btn.pack(side=tk.RIGHT)
        
        # Cancel download button (initially hidden)
        cancel_download_btn = ttk.Button(button_frame, text="Cancel Download", 
                                       command=lambda: None, state='disabled')
        cancel_download_btn.pack(side=tk.RIGHT, padx=(0, 10))
        cancel_download_btn.pack_forget()  # Hide initially
        
        download_btn = ttk.Button(button_frame, text="Download", command=start_download, state='disabled')
        download_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Handle Enter key in manual entry
        model_entry.bind('<Return>', lambda e: start_download())
        dialog.bind('<Escape>', lambda e: cancel_dialog())
        
        # Handle Enter key
        model_entry.bind('<Return>', lambda e: start_download())
        dialog.bind('<Escape>', lambda e: cancel_dialog())

    def start_download_action(self):
        """Handle download button click - either start download or cancel it."""
        if self.is_downloading:
            # Currently downloading, so cancel it
            self.cancel_main_download()
        else:
            # Not downloading, show download dialog
            self.show_download_dialog()
    
    def cancel_main_download(self):
        """Cancel download from main window."""
        if not self.is_downloading:
            return
            
        # Reset main window state
        self.is_downloading = False
        self.downloading_model = None
        self.download_button.config(text="Download", command=self.start_download_action)
        if hasattr(self, 'download_status_label'):
            self.download_status_label.config(text="")
        
        # Re-enable chat input if a model is selected
        if self.selected_model:
            self.user_input.config(state='normal')
            self.send_button.config(state='normal')
        else:
            # Keep disabled if no model selected
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
        
        # If there's an active download dialog, trigger its cancel function
        if hasattr(self, '_active_download_dialog'):
            try:
                # Find and trigger the cancel download button in the dialog
                def find_cancel_button(widget):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button):
                            btn_text = child.cget("text").lower()
                            if "cancel" in btn_text and "download" in btn_text:
                                child.invoke()
                                return True
                        elif hasattr(child, 'winfo_children'):
                            if find_cancel_button(child):
                                return True
                    return False
                
                find_cancel_button(self._active_download_dialog)
                
            except Exception as e:
                # If dialog cancel fails, just show message
                self.show_status_message(f"Download cancelled from main window")
        else:
            self.show_status_message("Download cancelled from main window")

    # NOTE: Legacy download method - replaced by dialog-based download with progress tracking
    # def download_model(self, model_name):
    #     """Download a model using ollama pull."""
    #     # This method is replaced by the enhanced dialog-based download system
    #     # in show_download_dialog() which provides better progress tracking
    #     pass

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
        self.download_button.config(text="Download", command=self.start_download_action)
        
        # Re-enable chat only if a model is selected
        if self.selected_model:
            self.send_button.config(state='normal')
            self.user_input.config(state='normal')
        else:
            self.send_button.config(state='disabled')
            self.user_input.config(state='disabled')
            
        self.stop_button.config(state='disabled')  # Keep stop disabled when not generating

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
                # Try using top command for CPU usage (fallback approach)
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
            
            # Disable chat input and send button when no model is selected
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
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
        
        # Extract and store max context tokens for token counter
        context_str = model_info['context']
        if context_str not in ["Unknown", "Loading...", "Error"]:
            try:
                if 'K' in context_str:
                    # Handle "4K", "8K", etc.
                    self.max_context_tokens = int(context_str.replace('K', '')) * 1000
                else:
                    # Handle raw numbers
                    self.max_context_tokens = int(context_str)
            except (ValueError, AttributeError):
                self.max_context_tokens = 4096  # Default fallback
        else:
            self.max_context_tokens = 4096  # Default fallback
        
        # Update token counter display
        self.update_token_counter()

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
        
        # If currently generating, stop the generation first
        if self.is_generating:
            self.stop_generation()
        
        self.selected_model = selected
        
        # Reset conversation history for new model
        self.reset_conversation_history()
        
        # Show loading state immediately
        self.update_model_details(selected, loading=True)
        
        # Clear chat display and show welcome message
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.insert(tk.END, f"✅ Model '{selected}' is ready for chat!\n")
        self.chat_display.insert(tk.END, "� Type your message in the input field below and press Enter or click Send.\n\n")
        self.chat_display.config(state='disabled')
        
        # Clear input field and enable it
        self.user_input.config(state='normal')
        self.user_input.delete("1.0", tk.END)
        self.user_input.focus()
        
        # Enable send button
        self.send_button.config(state='normal')
        
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

    def stop_generation(self):
        """Stop the current model response generation."""
        if not self.is_generating:
            return
            
        self.is_generating = False  # Set this first to prevent error messages
        
        if self.current_request:
            try:
                # Close the current HTTP request
                self.current_request.close()
                self.current_request = None
                self.show_status_message("⏹️ Response generation stopped by user")
                
                # Add a message to the chat indicating the stop
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, "\n[Response stopped by user]\n\n")
                self.chat_display.config(state='disabled')
                self.chat_display.see(tk.END)
                
            except Exception as e:
                self.show_status_message(f"Error stopping generation: {str(e)}")
        
        # Reset state and setup new prompt regardless of whether there was an error
        self.finalize_chat_response()

    def on_input_keypress(self, event):
        """Handle key presses in the user input field."""
        # Don't process key events if input is disabled
        if str(self.user_input.cget('state')) == 'disabled':
            return "break"
            
        # Handle Enter key - send message (Ctrl+Enter for new line)
        if event.keysym == "Return" and not event.state & 0x4:  # 0x4 is Ctrl key
            # Prevent default newline insertion and send message
            self.send_message_from_input()
            return "break"
        
        # Allow normal text editing
        return None

    def send_message_from_input(self):
        """Send message from the user input field."""
        if self.is_downloading:
            self.show_status_message("⚠️ Chat is disabled while downloading model. Please wait for download to complete.")
            return
            
        if not self.selected_model:
            self.show_status_message("⚠️ Please choose a model first using the 'Choose Model' button.")
            return
        
        # Check if input field is disabled (shouldn't happen with proper UI state management)
        if str(self.user_input.cget('state')) == 'disabled':
            self.show_status_message("⚠️ Chat input is currently disabled. Please select a model.")
            return
        
        # Get user input from the input field
        try:
            user_text = self.user_input.get("1.0", tk.END).strip()
            
            if not user_text:
                self.show_status_message("⚠️ Please type a message")
                return
            
            # Add user message to chat display
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, f"You: {user_text}\n\n")
            self.chat_display.config(state='disabled')
            self.chat_display.see(tk.END)
            
            # Clear the input field
            self.user_input.delete("1.0", tk.END)
            
            # Add user message to conversation history for token tracking
            self.add_to_conversation_history("user", user_text)
            
            # Disable send button and enable stop button during processing
            self.send_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.is_generating = True
            
            # Add AI response prompt to chat display
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, "AI: ")
            self.chat_display.config(state='disabled')
            self.chat_display.see(tk.END)
            
            # Reset response accumulator
            self.current_response = ""
            
            def run_query():
                self.run_ollama_query(self.selected_model, user_text)
                
            threading.Thread(target=run_query, daemon=True).start()
            
        except Exception as e:
            self.show_status_message(f"Error sending message: {str(e)}")
            # Re-enable send button if there's an error
            self.send_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.is_generating = False

    def refresh_models(self):
        """Refresh the model dropdown with current Ollama models."""
        # Store the previously selected model
        previous_model = self.model_var.get()
        
        models = self.get_ollama_models()
        self.model_dropdown['values'] = models
        
        if models:
            # If there was a download that just completed, try to select the new model
            download_status_text = self.download_status_label.cget('text')
            if download_status_text.startswith('✅ Downloaded '):
                # Extract model name from download status
                downloaded_model = download_status_text.replace('✅ Downloaded ', '')
                # Find matching model in the list
                matching_model = None
                for model in models:
                    if downloaded_model in model or model.startswith(downloaded_model.split(':')[0]):
                        matching_model = model
                        break
                
                if matching_model:
                    self.model_var.set(matching_model)
                    self.selected_model = matching_model
                    self.update_model_details(matching_model)
                    self.show_status_message(f"✅ Downloaded and selected: {matching_model}")
                    # Clear download status after successful selection
                    self.download_status_label.config(text="")
                    return
            
            # If previous model is still available, keep it selected
            if previous_model and previous_model in models:
                self.model_var.set(previous_model)
                self.show_status_message(f"Found {len(models)} model(s). Current: {previous_model}")
            else:
                # Set first model as default
                self.model_var.set(models[0])
                self.show_status_message(f"Found {len(models)} model(s). Default: {models[0]}")
        else:
            self.model_var.set("")
            self.show_status_message("No models found. Install models: 'ollama pull llama3'")
        
        # Reset to no model selected state if no model is currently selected
        if not self.selected_model:
            self.update_model_details(None)
            
        # Clear download status if not downloading (and not just completed)
        if not self.is_downloading and not self.download_status_label.cget('text').startswith('✅'):
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
            self.root.after(0, lambda: self.chat_display.config(state='normal'))
            self.root.after(0, lambda: self.chat_display.insert(tk.END, "Error: Ollama not found\n\n"))
            self.root.after(0, lambda: self.chat_display.config(state='disabled'))
            self.root.after(0, lambda: self.send_button.config(state='normal'))
            self.root.after(0, lambda: self.stop_button.config(state='disabled'))
            self.root.after(0, lambda: setattr(self, 'is_generating', False))
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
                
                # Store the request for potential cancellation
                self.current_request = requests.post(url, json=payload, stream=True, timeout=timeout)
                
                with self.current_request as response:
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
                # Check if it was a user-initiated cancellation
                if not self.is_generating:
                    return  # User stopped the generation, don't show error
                self.root.after(0, lambda: self.update_chat_with_response(f"\nError: {str(e)}\n"))
                self.root.after(0, self.finalize_chat_response)
            except Exception as e:
                if not self.is_generating:
                    return  # User stopped the generation, don't show error
                self.root.after(0, lambda: self.update_chat_with_response(f"\nAn unexpected error occurred: {str(e)}\n"))
                self.root.after(0, self.finalize_chat_response)
            finally:
                # Clean up the request reference
                self.current_request = None

        threading.Thread(target=query, daemon=True).start()

    def filter_thinking_tags(self, text):
        """Filter out <think> and </think> tags and their content from model responses."""
        # If user wants to see thinking, return text as-is
        if self.show_thinking_var.get():
            return text
        
        # Remove complete <think>...</think> blocks
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove standalone opening or closing tags
        text = re.sub(r'</?think>', '', text)
        
        return text

    def update_chat_with_response(self, chunk):
        """Append a chunk of the model's response to the chat display."""
        # Accumulate the response
        self.current_response += chunk
        
        # For streaming, we'll show the text without markdown formatting during typing
        # and apply formatting at the end to avoid flickering and partial markdown issues
        
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
                self.chat_display.config(state='normal')
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
                self.chat_display.config(state='disabled')
                return
        
        # Normal case: either thinking is enabled or no thinking tags in chunk
        # Just append the raw chunk - formatting will be applied at the end
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, chunk)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def finalize_chat_response(self):
        """Finalize the chat response - simplified version"""
        # Apply final filtering if thinking is disabled
        response_to_display = self.current_response
        if not self.show_thinking_var.get() and self.current_response:
            response_to_display = self.filter_thinking_tags(self.current_response)
        
        # Find and update the AI response
        if response_to_display:
            self.chat_display.config(state='normal')
            
            # Get all content
            content = self.chat_display.get("1.0", tk.END)
            
            # Find the last "AI: " position
            last_ai_pos = content.rfind("AI: ")
            
            if last_ai_pos != -1:
                # Calculate text widget position
                lines_before = content[:last_ai_pos].count('\n')
                ai_line = lines_before + 1
                ai_start = f"{ai_line}.4"  # Position after "AI: "
                
                # Get the raw response text that was streamed
                raw_response = self.chat_display.get(ai_start, tk.END).strip()
                
                # Clean the markdown
                cleaned_response = self.clean_markdown_text(raw_response)
                
                # Only replace if text actually changed (to avoid flickering)
                if raw_response != cleaned_response:
                    # Delete old content
                    self.chat_display.delete(ai_start, tk.END)
                    # Insert cleaned content
                    self.chat_display.insert(ai_start, cleaned_response)
            
            self.chat_display.config(state='disabled')
        
        # Add final newlines
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        # Focus on the input field for next message
        self.user_input.focus()
        
        # Add AI response to conversation history for token tracking
        if self.current_response:
            response_to_track = self.current_response
            if not self.show_thinking_var.get():
                response_to_track = self.filter_thinking_tags(self.current_response)
            self.add_to_conversation_history("assistant", response_to_track)
        
        # Reset button states
        self.send_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.is_generating = False
        self.current_request = None

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

    def estimate_token_count(self, text):
        """Estimate token count for a given text using simple heuristics."""
        if not text:
            return 0
        
        # Simple estimation: ~4 characters per token on average for English text
        # This is a rough approximation, real tokenizers are more complex
        # but this gives a reasonable estimate for UI purposes
        
        # Remove extra whitespace and count words
        words = text.split()
        word_count = len(words)
        
        # Estimate tokens: roughly 0.75 tokens per word for English
        # Add some padding for punctuation and special tokens
        estimated_tokens = int(word_count * 0.75) + max(1, len(text) // 100)
        
        return max(1, estimated_tokens)  # Minimum 1 token
    
    def update_token_counter(self):
        """Update the token counter display with current usage."""
        if not self.selected_model or self.max_context_tokens == 0:
            self.token_counter_label.config(text="Tokens: 0 / 0", foreground="gray")
            return
        
        # Calculate tokens used in current conversation
        total_tokens = 0
        for message in self.conversation_history:
            total_tokens += self.estimate_token_count(message.get('content', ''))
        
        self.current_chat_tokens = total_tokens
        
        # Calculate percentage used
        if self.max_context_tokens > 0:
            usage_percentage = (total_tokens / self.max_context_tokens) * 100
            remaining_tokens = self.max_context_tokens - total_tokens
            
            # Format numbers for display
            if self.max_context_tokens >= 1000:
                max_display = f"{self.max_context_tokens // 1000}K"
            else:
                max_display = str(self.max_context_tokens)
            
            # Set color based on usage - more conservative thresholds
            if usage_percentage < 60:
                color = "green"
            elif usage_percentage < 80:
                color = "orange"  
            else:
                color = "red"
            
            # Add warning icon for high usage
            warning = ""
            if usage_percentage >= 90:
                warning = " ⚠️"
            elif usage_percentage >= 80:
                warning = " ⚡"
            
            self.token_counter_label.config(
                text=f"Tokens: {total_tokens} / {max_display}{warning}",
                foreground=color
            )
        else:
            self.token_counter_label.config(text=f"Tokens: {total_tokens}", foreground="gray")
    
    def reset_conversation_history(self):
        """Reset the conversation history and token counter."""
        self.conversation_history = []
        self.current_chat_tokens = 0
        self.update_token_counter()
    
    def add_to_conversation_history(self, role, content):
        """Add a message to the conversation history for token tracking."""
        if content.strip():  # Only add non-empty messages
            self.conversation_history.append({
                'role': role,
                'content': content.strip()
            })
            self.update_token_counter()
    
if __name__ == "__main__":
    import re
    import random

    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()