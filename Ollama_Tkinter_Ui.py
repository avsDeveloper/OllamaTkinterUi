#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import sys
import platform
import requests
import json
import re
import webbrowser
import getpass

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter GUI for Ollama - Chat Mode")
        self.root.geometry("1400x900")

        # Menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Model Parameters", command=self.show_settings_dialog)
        
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
        left_frame = ttk.Frame(content_frame, width=400)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)  # Maintain fixed width
        
        # Right panel for chat
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Server Status Section (in left panel)
        server_section_frame = ttk.Frame(left_frame)
        server_section_frame.pack(pady=(0, 10), fill=tk.X)
        
        # Server section header
        server_header = ttk.Label(server_section_frame, text="Ollama Server:", 
                                 font=('Arial', 10, 'bold'))
        server_header.pack(anchor='w', pady=(0, 5))
        
        # Server status frame (status + restart button on same line)
        server_status_frame = ttk.Frame(server_section_frame)
        server_status_frame.pack(fill=tk.X)
        
        # Server status label
        self.server_status_label = ttk.Label(server_status_frame, 
                                           text="Server Status: Checking...", 
                                           foreground="#1976D2", 
                                           font=('Arial', 10))
        self.server_status_label.pack(side=tk.LEFT, anchor='w')
        
        # Restart button at the end of status line
        self.restart_button = ttk.Button(server_status_frame, text="Restart", command=self.restart_ollama_server)
        self.restart_button.pack(side=tk.RIGHT)

        # Model Selection (in left panel)
        self.model_label = ttk.Label(left_frame, text="Select Model:")
        self.model_label.pack(pady=(0, 5), anchor='w')
        
        # Model dropdown and buttons frame
        model_frame = ttk.Frame(left_frame)
        model_frame.pack(pady=(0, 10), fill=tk.X)
        
        self.model_var = tk.StringVar()
        self.model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var, width=25, state="readonly")
        self.model_dropdown.pack(fill=tk.X, pady=(0, 5))
        
        # Don't bind automatic selection to dropdown - user must click Choose Model button
        # Just ensure we save the selection in case the app closes
        self.model_dropdown.bind('<<ComboboxSelected>>', lambda e: self.save_settings())
        
        buttons_frame = ttk.Frame(model_frame)
        buttons_frame.pack(fill=tk.X)
        
        self.refresh_button = ttk.Button(buttons_frame, text="Refresh", command=self.refresh_models)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.choose_button = ttk.Button(buttons_frame, text="Choose Model", command=self.choose_model)
        self.choose_button.pack(side=tk.LEFT)
        
        # Add download state tracking
        self.is_downloading = False
        self.downloading_model = None
        
        # Add model status tracking
        self.model_status = "Not selected"  # Possible values: "Not selected", "Loading", "Ready", "Error"
        
        self.download_button = ttk.Button(buttons_frame, text="Manage Models", command=self.start_download_action)
        self.download_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Download status label
        self.download_status_label = ttk.Label(model_frame, text="", foreground="#1976D2", font=('Arial', 9))
        self.download_status_label.pack(pady=(5, 0), anchor='w')
        
        # Model details display - fixed height container to prevent UI jumping (always 6 lines)
        self.model_details_container = ttk.Frame(model_frame, height=120)  # Fixed height for 6 lines
        self.model_details_container.pack(pady=(2, 0), fill=tk.X)
        self.model_details_container.pack_propagate(False)  # Prevent shrinking
        
        # Create 6 fixed lines for model details (always visible) - first line for status
        self.model_detail_lines = []
        for i in range(6):
            line_label = ttk.Label(self.model_details_container, text="", 
                                 foreground="green", font=('Arial', 9))
            line_label.pack(anchor='w')
            self.model_detail_lines.append(line_label)
        
        # Set initial state - no model selected
        self.model_detail_lines[0].config(text="Model status: Not selected", foreground="red")
        # Leave other lines empty initially
        
        # Mode Selection Section (in left panel, after model selection)
        mode_frame = ttk.Frame(left_frame)
        mode_frame.pack(pady=(10, 0), fill=tk.X)
        
        mode_label = ttk.Label(mode_frame, text="Mode:", font=('Arial', 10, 'bold'))
        mode_label.pack(anchor='w', pady=(0, 5))
        
        # Mode toggle buttons
        mode_buttons_frame = ttk.Frame(mode_frame)
        mode_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.chat_button = ttk.Button(mode_buttons_frame, text="💬 Chat", command=self.switch_to_chat_mode)
        self.chat_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.translator_button = ttk.Button(mode_buttons_frame, text="🌐 Translator", command=self.switch_to_translator_mode)
        self.translator_button.pack(side=tk.LEFT)
        
        # Fixed space container for translation settings (always visible to maintain layout)
        translation_container = ttk.Frame(mode_frame)
        translation_container.pack(fill=tk.X, pady=(0, 10))
        
        # Translator settings frame (always visible but may be disabled)
        self.translator_frame = ttk.LabelFrame(translation_container, text="Translation Settings", padding=10)
        self.translator_frame.pack(fill=tk.X)  # Always pack, but may be disabled
        
        # Source language
        self.from_label = ttk.Label(self.translator_frame, text="From:")
        self.from_label.grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.source_lang_var = tk.StringVar(value="English")
        self.source_lang_combo = ttk.Combobox(self.translator_frame, textvariable=self.source_lang_var, 
                                             values=self.get_language_list(), width=12, state="readonly")
        self.source_lang_combo.grid(row=0, column=1, sticky='w', padx=(0, 5))
        
        # Target language
        self.to_label = ttk.Label(self.translator_frame, text="To:")
        self.to_label.grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.target_lang_var = tk.StringVar(value="Spanish")
        self.target_lang_combo = ttk.Combobox(self.translator_frame, textvariable=self.target_lang_var,
                                             values=self.get_language_list(), width=12, state="readonly")
        self.target_lang_combo.grid(row=0, column=3, sticky='w')
        
        # Swap languages button
        self.swap_button = ttk.Button(self.translator_frame, text="⇄", command=self.swap_languages, width=3)
        self.swap_button.grid(row=1, column=1, columnspan=2, pady=(5, 0))
        
        # Auto-detect option
        self.auto_detect_var = tk.BooleanVar(value=False)
        self.auto_detect_check = ttk.Checkbutton(self.translator_frame, text="Auto-detect source language", 
                                               variable=self.auto_detect_var)
        self.auto_detect_check.grid(row=2, column=0, columnspan=4, sticky='w', pady=(5, 0))
        
        # Translation style
        self.style_label = ttk.Label(self.translator_frame, text="Style:")
        self.style_label.grid(row=3, column=0, sticky='w', pady=(5, 0), padx=(0, 5))
        self.translation_style_var = tk.StringVar(value="Natural")
        self.style_combo = ttk.Combobox(self.translator_frame, textvariable=self.translation_style_var,
                                      values=["Natural", "Formal", "Casual", "Technical", "Literary"], 
                                      width=12, state="readonly")
        self.style_combo.grid(row=3, column=1, columnspan=2, sticky='w', pady=(5, 0))
        
        # Configure grid columns to expand properly
        self.translator_frame.grid_columnconfigure(1, weight=1)
        self.translator_frame.grid_columnconfigure(3, weight=1)
        
        # Store all translation widgets for enable/disable functionality
        self.translation_widgets = [
            self.source_lang_combo, self.target_lang_combo, self.swap_button,
            self.auto_detect_check, self.style_combo
        ]
        
        # Bind events to save settings when translation preferences change
        self.source_lang_combo.bind('<<ComboboxSelected>>', lambda e: self.save_settings())
        self.target_lang_combo.bind('<<ComboboxSelected>>', lambda e: self.save_settings())
        self.auto_detect_check.bind('<Button-1>', lambda e: self.root.after(10, self.save_settings))
        self.style_combo.bind('<<ComboboxSelected>>', lambda e: self.save_settings())
        
        # Logs section (in left panel)
        logs_label = ttk.Label(left_frame, text="System Logs:")
        logs_label.pack(pady=(20, 5), anchor='w')
        
        self.logs_display = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=40, height=25, font=('Consolas', 9))
        self.logs_display.pack(fill=tk.BOTH, expand=True)
        
        # Chat Display (in right panel)
        self.right_panel_content = ttk.Frame(right_frame)
        self.right_panel_content.pack(fill=tk.BOTH, expand=True)
        
        # Chat Mode Interface
        self.chat_interface = ttk.Frame(self.right_panel_content)
        self.chat_interface.pack(fill=tk.BOTH, expand=True)
        
        chat_label = ttk.Label(self.chat_interface, text="Chat:")
        chat_label.pack(pady=(0, 5), anchor='w')
        
        # Chat history display (read-only) with enhanced formatting support
        self.chat_display = scrolledtext.ScrolledText(self.chat_interface, wrap=tk.WORD, font=('Arial', 11), 
                                                    state='disabled', bg='#FFFFFF', fg='#333333',
                                                    selectbackground='#0078D4', selectforeground='white')
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure text tags for rich formatting
        self.setup_chat_formatting()
        
        # User input frame
        input_frame = ttk.Frame(self.chat_interface)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # User input label
        input_label = ttk.Label(input_frame, text="Your message (Enter for new line, Ctrl+Enter to send):")
        input_label.pack(anchor='w', pady=(0, 5))
        
        # User input entry
        self.user_input = tk.Text(input_frame, height=3, font=('Arial', 11), wrap=tk.WORD, state='disabled')
        self.user_input.pack(fill=tk.X, pady=(0, 5))
        self.user_input.bind("<KeyPress>", self.on_input_keypress)

        # Send button (in chat interface)
        button_frame = ttk.Frame(self.chat_interface)
        button_frame.pack(pady=(0, 5))
        
        self.send_button = ttk.Button(button_frame, text="Send Message (Ctrl+Enter)", command=self.send_message_from_input, state='disabled')
        self.send_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_generation, state='disabled')
        self.stop_button.pack(side=tk.LEFT)
        
        # Token counter display (bottom-right)
        self.token_counter_label = ttk.Label(button_frame, text="Tokens: 0 / 0", 
                                           font=('Arial', 10, 'bold'), foreground="gray")
        self.token_counter_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Translator Mode Interface (initially hidden)
        self.translator_interface = ttk.Frame(self.right_panel_content)
        
        translator_title = ttk.Label(self.translator_interface, text="Translation", font=('Arial', 14, 'bold'))
        translator_title.pack(pady=(0, 10), anchor='w')
        
        # Input text frame
        input_text_frame = ttk.LabelFrame(self.translator_interface, text="Text to Translate (Enter for new line, Ctrl+Enter to translate)", padding=10)
        input_text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.translation_input = scrolledtext.ScrolledText(input_text_frame, wrap=tk.WORD, font=('Arial', 11), 
                                                          height=8, bg='#FFFFFF', fg='#333333')
        self.translation_input.pack(fill=tk.BOTH, expand=True)
        self.translation_input.bind("<KeyRelease>", self.on_translation_input_change)
        self.translation_input.bind("<KeyPress>", self.on_translation_keypress)
        
        # Translation buttons frame
        translate_buttons_frame = ttk.Frame(self.translator_interface)
        translate_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.translate_button = ttk.Button(translate_buttons_frame, text="🌐 Translate (Ctrl+Enter)", 
                                          command=self.translate_text, state='disabled')
        self.translate_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_translation_button = ttk.Button(translate_buttons_frame, text="🗑️ Clear", 
                                                  command=self.clear_translation)
        self.clear_translation_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.copy_translation_button = ttk.Button(translate_buttons_frame, text="📋 Copy Result", 
                                                 command=self.copy_translation_result, state='disabled')
        self.copy_translation_button.pack(side=tk.LEFT)
        
        # Translation stop button
        self.translation_stop_button = ttk.Button(translate_buttons_frame, text="Stop", 
                                                 command=self.stop_generation, state='disabled')
        self.translation_stop_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Output text frame
        output_text_frame = ttk.LabelFrame(self.translator_interface, text="Translation Result", padding=10)
        output_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.translation_output = scrolledtext.ScrolledText(output_text_frame, wrap=tk.WORD, font=('Arial', 11), 
                                                           height=8, bg='#F8F9FA', fg='#333333', state='disabled')
        self.translation_output.pack(fill=tk.BOTH, expand=True)
        
        # Hide translator interface initially
        self.translator_interface.pack_forget()
        
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

        # Settings file path - in same directory as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(script_dir, "ollama_gui_settings.json")

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
        
        # Model settings variables
        self.response_timeout_var = tk.StringVar(value="60")  # Default timeout is 60 seconds
        self.show_thinking_var = tk.BooleanVar(value=False)  # Default: hide thinking
        self.temperature_var = tk.DoubleVar(value=0.7)  # Default temperature
        self.top_p_var = tk.DoubleVar(value=0.9)  # Default top_p
        self.top_k_var = tk.IntVar(value=40)  # Default top_k
        self.repeat_penalty_var = tk.DoubleVar(value=1.1)  # Default repeat penalty
        self.max_tokens_var = tk.IntVar(value=0)  # 0 means no limit
        self.seed_var = tk.IntVar(value=-1)  # -1 means random seed
        
        # Token tracking variables
        self.current_chat_tokens = 0  # Tokens used in current conversation
        self.max_context_tokens = 0  # Maximum context window for current model
        self.conversation_history = []  # Store conversation for token counting
        
        # Model information cache
        self.model_info_cache = {}  # Cache for model size and info
        
        # Translation mode variables
        self.is_translator_mode = False
        self.translation_in_progress = False
        
        # Initialize token counter display
        self.update_token_counter()
        
        # Set initial mode appearance
        self.update_mode_buttons()
        
        # Set initial translation settings state (disabled in chat mode)
        self.set_translation_settings_state('disabled')
        
        # Load saved settings from file
        self.load_settings()

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
        """Find the full path to ollama executable in a cross-platform way."""
        # Get platform-specific paths
        if platform.system() == "Windows":
            common_paths = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Ollama", "ollama.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Ollama", "ollama.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Ollama", "ollama.exe"),
                os.path.join(os.environ.get("APPDATA", ""), "Ollama", "ollama.exe"),
                "ollama.exe"  # Search in PATH
            ]
        elif platform.system() == "Darwin":  # macOS
            common_paths = [
                "/usr/local/bin/ollama",
                "/opt/homebrew/bin/ollama",
                os.path.expanduser("~/ollama"),
                os.path.expanduser("~/.ollama/ollama"),
                os.path.expanduser("~/Applications/Ollama.app/Contents/MacOS/ollama"),
                "/Applications/Ollama.app/Contents/MacOS/ollama"
            ]
        else:  # Linux and other Unix-like systems
            common_paths = [
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
                "/opt/ollama/bin/ollama",
                "/snap/bin/ollama",
                os.path.expanduser("~/.local/bin/ollama")
            ]
        
        # Try common paths first
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return path
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
        
        # Try to find ollama in user's shell environment
        try:
            # Platform-specific command to locate executable in PATH
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", "ollama"], 
                    capture_output=True, text=True, timeout=5
                )
            elif platform.system() in ["Darwin", "Linux"]:
                # Use shell's which command
                shell_cmd = ["which", "ollama"]
                result = subprocess.run(
                    shell_cmd, 
                    capture_output=True, text=True, timeout=5
                )
            if result.returncode == 0 and result.stdout.strip():
                ollama_path = result.stdout.strip()
                # Verify it works
                test_result = subprocess.run([ollama_path, "--version"], capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    return ollama_path
        except Exception as e:
            self.show_status_message(f"Error finding Ollama in PATH: {str(e)}")
        
        # Final fallback - try "ollama" directly in PATH
        try:
            # Determine executable name based on platform
            executable_name = "ollama.exe" if platform.system() == "Windows" else "ollama"
            result = subprocess.run([executable_name, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return executable_name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        self.show_status_message(f"Could not find Ollama on this {platform.system()} system")
        return None

    def is_ollama_server_running(self):
        """Check if Ollama server is running in a cross-platform way"""
        try:
            if not self.ollama_path:
                return False
                
            # The 'list' command works cross-platform to check if server is responding
            subprocess.run([self.ollama_path, "list"], 
                         check=True, capture_output=True, text=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            # For debugging server connectivity issues
            self.show_status_message(f"Server check failed: {type(e).__name__}")
            return False
    
    def detect_server_starter(self):
        """Detect who started the Ollama server process in a cross-platform way."""
        try:
            # Get current user info
            current_user = getpass.getuser()
            
            # Different approaches based on platform
            if platform.system() == "Windows":
                # On Windows, use tasklist to find processes
                try:
                    task_result = subprocess.run(
                        ["tasklist", "/FI", "IMAGENAME eq ollama.exe", "/V", "/FO", "CSV"],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if task_result.returncode == 0 and "ollama.exe" in task_result.stdout:
                        # On Windows, for simplicity, we'll always consider it user-started if running
                        self.show_status_message("Ollama server detected on Windows")
                        return True
                    
                except Exception as e:
                    self.show_status_message(f"Windows process detection error: {str(e)}")
                    return False
                    
            elif platform.system() == "Darwin":  # macOS
                try:
                    # On macOS, use ps to find processes
                    ps_result = subprocess.run(
                        ["ps", "-ef"], 
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.split('\n')
                        for line in lines:
                            if 'ollama serve' in line:
                                parts = line.split()
                                if len(parts) >= 3:
                                    process_user = parts[0]
                                    self.show_status_message(f"Found ollama serve process running as: {process_user}")
                                    
                                    # Check if it's the current user
                                    if process_user == current_user:
                                        return True  # Started by user
                                    else:
                                        return False  # Started by system or another user
                
                except Exception as e:
                    self.show_status_message(f"macOS process detection error: {str(e)}")
            
            else:  # Linux and other Unix-like systems
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
                                    self.show_status_message(f"Found ollama serve process running as: {process_user}")
                                    
                                    # Check if it's the current user
                                    if process_user == current_user:
                                        return True  # Started by user
                                    elif process_user in ['root', 'ollama', 'systemd+', '_ollama']:
                                        return False  # Started by system
                                    else:
                                        # Could be another user, assume system for safety
                                        self.show_status_message(f"Unknown user '{process_user}', assuming system process")
                                        return False
                    
                    # Linux-specific fallback: try pgrep with user info
                    try:
                        pgrep_result = subprocess.run(
                            ["pgrep", "-f", "-u", current_user, "ollama serve"],
                            capture_output=True, text=True, timeout=3
                        )
                        
                        if pgrep_result.returncode == 0 and pgrep_result.stdout.strip():
                            self.show_status_message(f"ollama serve confirmed running as {current_user}")
                            return True
                        else:
                            # Check if it's running as system user
                            pgrep_system = subprocess.run(
                                ["pgrep", "-f", "ollama serve"],
                                capture_output=True, text=True, timeout=3
                            )
                            if pgrep_system.returncode == 0:
                                self.show_status_message("ollama serve found running as system process")
                                return False
                    except Exception:
                        # pgrep might not be available on all Linux distributions
                        pass
                        
                except Exception as e:
                    self.show_status_message(f"Linux process detection error: {str(e)}")
            
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

    def show_manage_models_dialog(self):
        """Show dialog for managing models - download new or delete existing models."""
        if self.is_downloading:
            return  # Prevent multiple manage dialogs
            
        # Create manage models dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Models")
        dialog.geometry("800x700")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"800x700+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Manage Ollama Models", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Download Models Tab
        download_frame = ttk.Frame(notebook)
        notebook.add(download_frame, text="Download Models")
        
        # Manage Installed Models Tab
        manage_frame = ttk.Frame(notebook)
        notebook.add(manage_frame, text="Manage Installed")
        
        # === DOWNLOAD MODELS TAB CONTENT ===
        download_content = ttk.Frame(download_frame, padding="10")
        download_content.pack(fill=tk.BOTH, expand=True)
        
        # Available models dropdown
        ttk.Label(download_content, text="Select from available models:").pack(anchor='w')
        
        # Status label for loading
        status_label = ttk.Label(download_content, text="Loading available models...", 
                                foreground="#1976D2", font=("Arial", 9))
        status_label.pack(anchor='w', pady=(2, 5))
        
        model_var = tk.StringVar()
        model_dropdown = ttk.Combobox(download_content, textvariable=model_var, width=50, state="readonly")
        model_dropdown.pack(fill=tk.X, pady=(0, 10))
        
        # Model size selection
        size_label = ttk.Label(download_content, text="Choose model size:")
        size_label.pack(anchor='w', pady=(10, 0))
        
        # Status label for size loading
        size_status_label = ttk.Label(download_content, text="Select a model first", 
                                     foreground="#666666", font=("Arial", 9))
        size_status_label.pack(anchor='w', pady=(2, 5))
        
        size_var = tk.StringVar()
        size_dropdown = ttk.Combobox(download_content, textvariable=size_var, width=50, state="readonly")
        size_dropdown.pack(fill=tk.X, pady=(0, 5))
        size_dropdown.config(state='disabled')  # Initially disabled
        
        # Model already downloaded warning (initially hidden)
        already_downloaded_label = ttk.Label(download_content, text="", 
                                           foreground="red", font=("Arial", 9, "bold"))
        already_downloaded_label.pack(anchor='w', pady=(0, 10))
        
        # Model information display (always visible)
        info_frame = ttk.Frame(download_content)
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
        ttk.Label(download_content, text="Or enter model name manually:").pack(anchor='w', pady=(20, 0))
        model_entry = ttk.Entry(download_content, width=50, font=("Arial", 11))
        model_entry.pack(fill=tk.X, pady=(5, 10))
        
        # Examples
        examples_label = ttk.Label(download_content, 
                                  text="Enter any model name from ollama.com/search",
                                  font=("Arial", 9), foreground="#666666")
        examples_label.pack(pady=(0, 20))
        
        # === MANAGE INSTALLED MODELS TAB CONTENT ===
        manage_content = ttk.Frame(manage_frame, padding="10")
        manage_content.pack(fill=tk.BOTH, expand=True)
        
        # Installed models section
        ttk.Label(manage_content, text="Installed Models:", font=("Arial", 12, "bold")).pack(anchor='w', pady=(0, 10))
        
        # Installed models listbox with scrollbar
        listbox_frame = ttk.Frame(manage_content)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create listbox with scrollbar
        installed_listbox = tk.Listbox(listbox_frame, font=("Arial", 10), height=12)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=installed_listbox.yview)
        installed_listbox.config(yscrollcommand=scrollbar.set)
        
        installed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Model details for selected installed model
        details_frame = ttk.LabelFrame(manage_content, text="Model Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Model details labels
        selected_model_label = ttk.Label(details_frame, text="No model selected", font=("Arial", 10, "bold"))
        selected_model_label.pack(anchor='w')
        
        model_size_label = ttk.Label(details_frame, text="", font=("Arial", 9))
        model_size_label.pack(anchor='w')
        
        model_modified_label = ttk.Label(details_frame, text="", font=("Arial", 9))
        model_modified_label.pack(anchor='w')
        
        # Action buttons for installed models
        action_frame = ttk.Frame(manage_content)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        refresh_installed_btn = ttk.Button(action_frame, text="🔄 Refresh List", command=lambda: refresh_installed_models())
        refresh_installed_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_model_btn = ttk.Button(action_frame, text="🗑️ Delete Selected", command=lambda: delete_selected_model(), state='disabled')
        delete_model_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label for manage operations
        manage_status_label = ttk.Label(manage_content, text="", font=("Arial", 9), foreground="#1976D2")
        manage_status_label.pack(anchor='w')
        
        # Functions for manage installed models tab
        def refresh_installed_models():
            """Refresh the list of installed models."""
            manage_status_label.config(text="Loading installed models...")
            installed_listbox.delete(0, tk.END)
            
            # Get installed models
            models = self.get_ollama_models()
            
            if models:
                for model in models:
                    installed_listbox.insert(tk.END, model)
                manage_status_label.config(text=f"Found {len(models)} installed model(s)")
            else:
                manage_status_label.config(text="No models found. Install models using the Download tab.")
            
            # Reset selection
            update_selected_model_details()
        
        def update_selected_model_details():
            """Update details for the selected model."""
            selection = installed_listbox.curselection()
            if selection:
                model_name = installed_listbox.get(selection[0])
                selected_model_label.config(text=f"Selected: {model_name}")
                delete_model_btn.config(state='normal')
                
                # Get model info
                model_info = self.get_model_info(model_name)
                model_size_label.config(text=f"Size: {model_info.get('size', 'Unknown')}")
                model_modified_label.config(text=f"Context: {model_info.get('context', 'Unknown')}")
            else:
                selected_model_label.config(text="No model selected")
                model_size_label.config(text="")
                model_modified_label.config(text="")
                delete_model_btn.config(state='disabled')
        
        def delete_selected_model():
            """Delete the selected model after confirmation."""
            selection = installed_listbox.curselection()
            if not selection:
                return
                
            model_name = installed_listbox.get(selection[0])
            
            # Confirm deletion
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete the model '{model_name}'?\n\n"
                f"This action cannot be undone. You will need to download the model again to use it.",
                icon='warning'
            )
            
            if result:
                # Perform deletion
                manage_status_label.config(text=f"Deleting {model_name}...")
                
                def delete_model():
                    try:
                        if not self.ollama_path:
                            dialog.after(0, lambda: manage_status_label.config(text="Error: Ollama not found"))
                            return
                        
                        # Use ollama rm command to delete the model
                        result = subprocess.run([self.ollama_path, "rm", model_name], 
                                              capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            dialog.after(0, lambda: manage_status_label.config(text=f"✅ Successfully deleted {model_name}"))
                            dialog.after(0, refresh_installed_models)
                            # If this was the currently selected model in main window, clear it
                            if hasattr(self, 'selected_model') and self.selected_model == model_name:
                                dialog.after(0, lambda: setattr(self, 'selected_model', None))
                                dialog.after(0, lambda: self.update_model_details(None))
                                dialog.after(0, lambda: self.model_var.set(""))
                            # Refresh main window model list
                            dialog.after(0, self.refresh_models)
                        else:
                            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                            dialog.after(0, lambda: manage_status_label.config(text=f"❌ Failed to delete {model_name}: {error_msg}"))
                    except subprocess.TimeoutExpired:
                        dialog.after(0, lambda: manage_status_label.config(text=f"❌ Deletion timed out for {model_name}"))
                    except Exception as e:
                        dialog.after(0, lambda: manage_status_label.config(text=f"❌ Error deleting {model_name}: {str(e)}"))
                
                # Run deletion in background thread
                threading.Thread(target=delete_model, daemon=True).start()
        
        # Bind listbox selection event
        installed_listbox.bind('<<ListboxSelect>>', lambda e: update_selected_model_details())
        
        # Load installed models initially
        dialog.after(100, refresh_installed_models)
        
        # Button frame (moved to main_frame bottom with padding)
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
            
            # Re-enable chat input only if a model is selected AND ready
            if (hasattr(self, 'selected_model') and self.selected_model and 
                hasattr(self, 'model_status') and self.model_status == "Ready"):
                if hasattr(self, 'user_input'):
                    self.user_input.config(state='normal')
                if hasattr(self, 'send_button'):
                    self.send_button.config(state='normal')
            else:
                # Keep disabled if no model selected or model not ready
                if hasattr(self, 'user_input'):
                    self.user_input.config(state='disabled')
                if hasattr(self, 'send_button'):
                    self.send_button.config(state='disabled')
        
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
        progress_frame = ttk.Frame(download_content)
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
        """Handle manage models button click - either manage models or cancel download."""
        if self.is_downloading:
            # Currently downloading, so cancel it
            self.cancel_main_download()
        else:
            # Not downloading, show manage models dialog
            self.show_manage_models_dialog()
    
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
        
        # Re-enable chat input only if a model is selected AND ready
        if (self.selected_model and hasattr(self, 'model_status') and 
            self.model_status == "Ready"):
            self.user_input.config(state='normal')
            self.send_button.config(state='normal')
        else:
            # Keep disabled if no model selected or model not ready
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
        
        # Re-enable chat only if a model is selected AND ready
        if (self.selected_model and hasattr(self, 'model_status') and 
            self.model_status == "Ready"):
            self.send_button.config(state='normal')
            self.user_input.config(state='normal')
        else:
            self.send_button.config(state='disabled')
            self.user_input.config(state='disabled')
            
        self.stop_button.config(state='disabled')  # Keep stop disabled when not generating

    def auto_start_server(self):
        """Automatically start the Ollama server if not running, in a cross-platform way."""
        if self.server_starting or not self.ollama_path:
            return
            
        self.server_starting = True
        # Mark that this GUI is starting the server
        self.server_started_by_user = True
        self.show_status_message(f"Starting Ollama server on {platform.system()}...")
        
        def start_server():
            try:
                self.root.after(0, lambda: self.show_status_message(f"Launching ollama serve command with {self.ollama_path}..."))
                
                # Platform-specific process creation
                if platform.system() == "Windows":
                    # On Windows, use creationflags to hide the console window
                    from subprocess import CREATE_NO_WINDOW
                    self.ollama_process = subprocess.Popen(
                        [self.ollama_path, "serve"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        creationflags=CREATE_NO_WINDOW
                    )
                else:
                    # On Unix-like systems, use start_new_session
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
            result = subprocess.run([self.ollama_path, "show", model_name], 
                                  capture_output=True, text=True, timeout=10)
            
            model_info = {"size": "Unknown", "ram_usage": "Unknown", "gpu_cpu_usage": "Unknown", "context": "Unknown"}
            
            if result.returncode == 0:
                output = result.stdout
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
                        break
                
                # Parse context window - look for various context patterns
                # Context tokens are different from model parameters!
                context_patterns = [
                    # Patterns for context values with K/M/B suffixes (tokens, not parameters)
                    r'context(?:\s+(?:length|size|window))?[:\s]+(\d+(?:\.\d+)?)\s*([kmb])\s*(?:tokens?)?',  # "context length: 131k tokens"
                    r'max(?:imum)?[_\s]?context[:\s]+(\d+(?:\.\d+)?)\s*([kmb])\s*(?:tokens?)?',  # "max_context: 1.5m tokens"
                    r'context[_\s]?(?:size|window)[:\s]+(\d+(?:\.\d+)?)\s*([kmb])\s*(?:tokens?)?',  # "context_size: 2b tokens"
                    r'num_ctx[:\s]+(\d+(?:\.\d+)?)\s*([kmb])\s*(?:tokens?)?',  # "num_ctx: 131k tokens"
                    r'(\d+(?:\.\d+)?)\s*([kmb])\s*(?:token|context)',  # "131k token context"
                    
                    # Patterns for raw context numbers (not parameters)
                    r'context(?:\s+(?:length|size|window))?[:\s]+(\d+)(?:\s+tokens?)?',  # "context length: 4096" or "context: 4096 tokens"
                    r'max(?:imum)?[_\s]?context[:\s]+(\d+)(?:\s+tokens?)?',  # "max_context: 4096"
                    r'context[_\s]?(?:size|window)[:\s]+(\d+)(?:\s+tokens?)?',  # "context_size: 4096"
                    r'num_ctx[:\s]+(\d+)(?:\s+tokens?)?',  # "num_ctx: 4096"
                    r'(\d+)\s*(?:token|k)\s*context',  # "4096 token context"
                    
                    # Common context window sizes to help identify them
                    r'(?:context|window|tokens?).*?(\d+)\s*k(?:\s+tokens?)?',  # "context window of 8k tokens"
                    r'(?:supports?|up\s+to)\s+(\d+)\s*k\s*(?:token|context)',  # "supports 32k context"
                ]
                
                for pattern in context_patterns:
                    match = re.search(pattern, output_lower)
                    if match:
                        if len(match.groups()) == 2:
                            # Pattern matched with suffix (K/M/B)
                            value = float(match.group(1))
                            suffix = match.group(2).lower()
                            
                            if suffix == 'k':
                                context_size = int(value * 1000)
                            elif suffix == 'm':
                                context_size = int(value * 1000000)
                            elif suffix == 'b':
                                context_size = int(value * 1000000000)
                            else:
                                context_size = int(value)
                        else:
                            # Pattern matched raw number
                            context_size = int(match.group(1))
                        
                        # Validate that this looks like a context size, not parameter count
                        # Context windows are typically 1K-2M tokens, parameter counts are typically 1B-405B
                        if context_size < 1000:
                            # Very small numbers (like 7, 13, 70) are likely parameters, not context
                            continue
                        elif context_size > 10_000_000:
                            # Very large numbers (10M+) are likely parameters, not context tokens  
                            continue
                        
                        # Format the output consistently for context tokens
                        if context_size >= 1000000:
                            # 1M+ tokens: show as "1.2M" format
                            if context_size % 1000000 == 0:
                                model_info["context"] = f"{context_size//1000000}M"
                            else:
                                model_info["context"] = f"{context_size/1000000:.1f}M"
                        elif context_size >= 1000:
                            # 1K+ tokens: show as "131K" format  
                            if context_size % 1000 == 0:
                                model_info["context"] = f"{context_size//1000}K"
                            else:
                                model_info["context"] = f"{context_size/1000:.1f}K"
                        else:
                            # Less than 1000: show exact number
                            model_info["context"] = str(context_size)
                        break
            else:
                self.show_status_message(f"Unable to get model details: {result.stderr.strip()}")
            
            # Get current usage from ollama ps
            ps_result = subprocess.run([self.ollama_path, "ps"], 
                                     capture_output=True, text=True, timeout=5)
            
            if ps_result.returncode == 0:
                ps_output = ps_result.stdout
                
                # Look for the model name in the ps output
                model_base_name = model_name.split(':')[0]  # Remove tag if present
                
                for line in ps_output.split('\n'):
                    if model_base_name in line or model_name in line:
                        # Try to extract memory usage info for RAM with more flexible patterns
                        memory_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB|G|M)', line, re.IGNORECASE)
                        if memory_match:
                            memory_size = memory_match.group(1)
                            memory_unit = memory_match.group(2).upper()
                            # Normalize unit format
                            if memory_unit == "G":
                                memory_unit = "GB"
                            elif memory_unit == "M":
                                memory_unit = "MB"
                            model_info["ram_usage"] = f"~{memory_size} {memory_unit}"
                        else:
                            # If no memory info found but model is in ps output, consider it loaded
                            model_info["ram_usage"] = "~1.0 GB"  # Use default value
                        
                        # Try to extract CPU/GPU usage percentages
                        # Look for patterns like "38%/62%" or "GPU: 38% CPU: 62%"
                        gpu_cpu_patterns = [
                            r'(\d+)%[/\s]*(\d+)%',  # "38%/62%" or "38% 62%"
                            r'gpu[:\s]*(\d+)%[,\s]*cpu[:\s]*(\d+)%',  # "GPU: 38%, CPU: 62%"
                            r'(\d+)%\s*gpu[,\s]*(\d+)%\s*cpu',  # "38% GPU, 62% CPU"
                            r'gpu[:\s]*(\d+)[,\s]*cpu[:\s]*(\d+)',  # "GPU: 38, CPU: 62" (without %)
                            r'(\d+)%[/\s,]*(\d+)%',  # More flexible separator patterns
                            r'gpu[:\s]*(\d+).*?cpu[:\s]*(\d+)',  # Very flexible GPU/CPU pattern
                        ]
                        
                        usage_found = False
                        for pattern in gpu_cpu_patterns:
                            usage_match = re.search(pattern, line.lower())
                            if usage_match:
                                gpu_pct = usage_match.group(1)
                                cpu_pct = usage_match.group(2)
                                model_info["gpu_cpu_usage"] = f"{gpu_pct}%/{cpu_pct}%"
                                usage_found = True
                                break
                        
                        if not usage_found:
                            # Look for any single percentage that might indicate model activity
                            # Check for GPU-specific patterns first
                            gpu_patterns = [
                                r'gpu[:\s]*(\d+(?:\.\d+)?)%',  # "GPU: 45%"
                                r'(\d+(?:\.\d+)?)%\s*gpu',  # "45% GPU"
                                r'vram[:\s]*(\d+(?:\.\d+)?)%',  # "VRAM: 45%"
                                r'(\d+(?:\.\d+)?)%\s*vram',  # "45% VRAM"
                            ]
                            
                            # Check for CPU-specific patterns
                            cpu_patterns = [
                                r'cpu[:\s]*(\d+(?:\.\d+)?)%',  # "CPU: 45%"
                                r'(\d+(?:\.\d+)?)%\s*cpu',  # "45% CPU"
                                r'ram[:\s]*(\d+(?:\.\d+)?)%',  # "RAM: 45%"
                                r'(\d+(?:\.\d+)?)%\s*ram',  # "45% RAM"
                            ]
                            
                            # Generic patterns (without explicit GPU/CPU context)
                            generic_patterns = [
                                r'(\d+(?:\.\d+)?)%',  # Any percentage like "45%", "67.5%"
                                r'(\d+(?:\.\d+)?)\s*percent',  # "45 percent"
                                r'load[:\s]*(\d+(?:\.\d+)?)%',  # "load: 45%"
                                r'usage[:\s]*(\d+(?:\.\d+)?)%',  # "usage: 45%"
                            ]
                            
                            # Try GPU patterns first
                            for pattern in gpu_patterns:
                                gpu_match = re.search(pattern, line.lower())
                                if gpu_match:
                                    pct = gpu_match.group(1)
                                    model_info["gpu_cpu_usage"] = f"{pct}%/0%"
                                    usage_found = True
                                    break
                            
                            # If no GPU pattern found, try CPU patterns
                            if not usage_found:
                                for pattern in cpu_patterns:
                                    cpu_match = re.search(pattern, line.lower())
                                    if cpu_match:
                                        pct = cpu_match.group(1)
                                        model_info["gpu_cpu_usage"] = f"0%/{pct}%"
                                        usage_found = True
                                        break
                            
                            # If still no specific pattern found, use generic patterns
                            # Default to GPU usage for generic percentages (most common case)
                            if not usage_found:
                                for pattern in generic_patterns:
                                    generic_match = re.search(pattern, line.lower())
                                    if generic_match:
                                        pct = generic_match.group(1)
                                        # For generic percentages without context, assume GPU usage
                                        model_info["gpu_cpu_usage"] = f"{pct}%/0%"
                                        usage_found = True
                                        break
                        
                        if not usage_found:
                            # If model is in ps output but no usage patterns found,
                            # it's likely running but ollama ps doesn't show detailed usage
                            # For small models, this is often normal - show a positive indicator
                            model_info["gpu_cpu_usage"] = "Model running"
                        break
                else:
                    # Model not found in ps output, might be loading
                    model_info["ram_usage"] = "Loading"
                    # Don't show system usage as it's not model-specific
                    model_info["gpu_cpu_usage"] = "Model not loaded"
            else:
                self.show_status_message(f"Unable to get model status: {ps_result.stderr.strip()}")
                # Don't show system usage when we can't get model-specific data
                model_info["gpu_cpu_usage"] = "Unable to determine"
            
            return model_info
            
        except Exception as e:
            self.show_status_message(f"Error getting model info: {str(e)}")
            return {"size": "Error", "ram_usage": "Error", "gpu_cpu_usage": "Error", "context": "Error"}

    def update_model_details(self, model_name, loading=False, retry_count=0):
        """Update the model details display with information about the selected model."""
        
        # Check if this operation was cancelled (user switched models)
        if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
            getattr(self, 'current_loading_model', '') != model_name):
            return
        
        if not model_name:
            # Clear all lines first
            for line in self.model_detail_lines:
                line.config(text="", foreground="green")
            
            # No model selected state
            self.model_status = "Not selected"
            self.model_detail_lines[0].config(text="Model status: Not selected", foreground="red")
            # Leave the second line empty when no model is selected
            
            # Disable chat input and send button when no model is selected
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
            return
        
        short_name = model_name.split(':')[0] if ':' in model_name else model_name
        
        # Show loading state immediately
        if loading:
            # Clear all lines first
            for line in self.model_detail_lines:
                line.config(text="", foreground="green")
                
            self.model_status = "Loading"
            self.model_detail_lines[0].config(text="Model status: Loading", foreground="#1976D2")
            self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
            # Don't show model data during loading - keep other lines empty
            
            # Disable chat input and send button during loading
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
            return
        
        # Check again if operation was cancelled before proceeding
        if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
            getattr(self, 'current_loading_model', '') != model_name):
            return
        
        # First check if model is loaded using basic ollama ps check
        if self.is_model_loaded_basic(model_name):
            # Model appears to be loaded, now get detailed info asynchronously
            self.fetch_model_info_async(model_name)
        # Check if model was recently successfully preloaded according to our logs
        elif hasattr(self, 'preload_success_models') and model_name in self.preload_success_models:
            # Model was successfully preloaded, but might not be visible in ps yet
            # Force fetch model info anyway since we know it should be available
            self.show_status_message(f"Model '{model_name}' was preloaded, getting model info...")
            self.fetch_model_info_async(model_name)
        else:
            # Check if we're already in the preloading phase
            if getattr(self, 'preloading_model', False) and getattr(self, 'current_loading_model', '') == model_name:
                # We're already preloading this model, don't retry or start another preload
                # Just show loading status
                short_name = model_name.split(':')[0] if ':' in model_name else model_name
                self.model_status = "Loading"
                self.model_detail_lines[0].config(text="Model status: Loading", foreground="#1976D2")
                self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
                # Don't do any retries since preload is already happening
                self.show_status_message(f"Model '{model_name}' is currently being loaded...")
                return
                
            # Model might be loading or not loaded
            # Determine max retries based on model size
            max_retries = 5  # Default for small models (5 seconds)
            model_lower = model_name.lower()
            if any(size in model_lower for size in ['70b', '72b', '405b']):
                max_retries = 60  # 1 minute for very large models
            elif any(size in model_lower for size in ['13b', '14b', '27b', '30b', '34b']):
                max_retries = 45  # 45 seconds for large models  
            elif any(size in model_lower for size in ['7b', '8b', '9b']):
                max_retries = 30  # 30 seconds for medium models
            
            if retry_count < max_retries:
                # Check if operation was cancelled before retrying
                if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
                    getattr(self, 'current_loading_model', '') != model_name):
                    return
                
                # Only update UI if this is the first check (retry_count == 0)
                # or if current status is not already "Loading"
                if retry_count == 0 or getattr(self, 'model_status', '') != "Loading":
                    self.model_status = "Loading"
                    self.model_detail_lines[0].config(text="Model status: Loading", foreground="#1976D2")
                    self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
                    
                    # Keep chat disabled during loading
                    self.user_input.config(state='disabled')
                    self.send_button.config(state='disabled')
                    
                    # Clear model data lines during loading (only if not already cleared)
                    self.model_detail_lines[2].config(text="", foreground="green")
                    self.model_detail_lines[3].config(text="", foreground="green") 
                    self.model_detail_lines[4].config(text="", foreground="green")
                    self.model_detail_lines[5].config(text="", foreground="green")
                
                # Retry checking after a short delay in case model is still loading
                def retry_check():
                    # Check if operation wasn't cancelled before retrying
                    if (not getattr(self, 'model_loading_cancelled', False) or 
                        getattr(self, 'current_loading_model', '') == model_name):
                        self.update_model_details(model_name, loading=False, retry_count=retry_count + 1)
                
                # Schedule retry after 1 second
                self.root.after(1000, retry_check)
            else:
                # After max retries exceeded, keep showing loading instead of error
                # Large models may still be initializing
                if (not getattr(self, 'model_loading_cancelled', False) or 
                    getattr(self, 'current_loading_model', '') == model_name):
                    
                    # For large models, continue showing loading state instead of error
                    if any(size in model_lower for size in ['70b', '72b', '405b', '13b', '14b', '27b', '30b', '34b']):
                        self.model_status = "Loading"
                        self.model_detail_lines[0].config(text="Model status: Loading (large model may take longer)", foreground="#1976D2")
                        self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
                        
                        # Keep checking every 5 seconds for large models
                        def extended_check():
                            if (not getattr(self, 'model_loading_cancelled', False) or 
                                getattr(self, 'current_loading_model', '') == model_name):
                                # Reset retry count and continue checking
                                self.update_model_details(model_name, loading=False, retry_count=0)
                        
                        self.root.after(5000, extended_check)  # Check again in 5 seconds
                    else:
                        # For small models, we'll also continue showing loading and try to preload
                        self.model_status = "Loading"
                        self.model_detail_lines[0].config(text="Model status: Loading (initializing...)", foreground="#1976D2")
                        self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
                        
                        # Try preloading the model instead of showing error
                        self.show_status_message(f"Small model '{model_name}' not detected, trying to preload...")
                        
                        # Start preload in a new thread to avoid blocking
                        threading.Thread(target=self.preload_model_safe, args=(model_name,), daemon=True).start()
                    
                    # Keep chat disabled until model is ready
                    self.user_input.config(state='disabled')
                    self.send_button.config(state='disabled')
                    
                    # Clear model data lines when not ready
                    self.model_detail_lines[2].config(text="", foreground="green")
                    self.model_detail_lines[3].config(text="", foreground="green") 
                    self.model_detail_lines[4].config(text="", foreground="green")
                    self.model_detail_lines[5].config(text="", foreground="green")
    
    def is_model_loaded_basic(self, model_name):
        """Quick check if model is loaded using ollama ps or if recently successfully preloaded."""
        if not self.ollama_path:
            return False
            
        # Track how many times we've checked this model to avoid redundant logging
        if not hasattr(self, '_model_check_count'):
            self._model_check_count = {}
            
        # Check if this model is in the set of successfully preloaded models
        if hasattr(self, 'preload_success_models') and model_name in self.preload_success_models:
            # We explicitly know this was successfully loaded
            # Only log once or if it's been a while since last log
            model_check_key = f"preloaded_{model_name}"
            if model_check_key not in self._model_check_count:
                self.show_status_message(f"Model '{model_name}' was previously successfully loaded")
                self._model_check_count[model_check_key] = 1
            return True
            
        # Check if model was recently preloaded successfully based on timestamp
        if (hasattr(self, 'preloaded_models') and 
            model_name in self.preloaded_models and 
            (time.time() - self.preloaded_models[model_name]) < 300):  # Consider loaded if preloaded in last 5 minutes
            # Only log once or if it's been a while since last log
            model_check_key = f"timestamp_{model_name}"
            if model_check_key not in self._model_check_count:
                self.show_status_message(f"Model '{model_name}' was preloaded in the last 5 minutes")
                self._model_check_count[model_check_key] = 1
            return True
            
        try:
            # First try with ollama ps
            result = subprocess.run([self.ollama_path, "ps"], 
                                 capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and result.stdout.strip():
                model_base_name = model_name.split(':')[0]
                ps_lines = result.stdout.split('\n')
                
                # Skip header line and check model entries
                for line in ps_lines[1:]:  # Skip first line (header)
                    if line.strip():  # Skip empty lines
                        # Check if model name appears in this line
                        if model_base_name.lower() in line.lower() or model_name.lower() in line.lower():
                            # Consider the model loaded if it appears in the ps output
                            # Only log the first time we find it
                            model_check_key = f"ps_{model_name}"
                            if model_check_key not in self._model_check_count:
                                self.show_status_message(f"Found '{model_name}' in ollama ps output")
                                self._model_check_count[model_check_key] = 1
                            return True
            
            # If model is not found in ps output, try a quick ollama show as a backup check
            # This is because sometimes models are loaded but not visible in ps
            try:
                show_result = subprocess.run([self.ollama_path, "show", model_name], 
                                          capture_output=True, text=True, timeout=2)
                # If show command works without error and returns info, model is likely accessible
                if show_result.returncode == 0 and show_result.stdout.strip():
                    # Only log the first time we find it
                    model_check_key = f"show_{model_name}"
                    if model_check_key not in self._model_check_count:
                        self.show_status_message(f"Model '{model_name}' is accessible via 'ollama show'")
                        self._model_check_count[model_check_key] = 1
                    
                    # For small models, consider them successfully loaded without full verification
                    # Large models still need to go through the full preload_model process
                    model_lower = model_name.lower()
                    is_small_model = not any(size in model_lower for size in ['70b', '72b', '405b', '13b', '14b', '27b', '30b', '34b', '7b', '8b', '9b'])
                    
                    # Record this model as detected
                    if not hasattr(self, 'preloaded_models'):
                        self.preloaded_models = {}
                    self.preloaded_models[model_name] = time.time()
                    
                    # For small models, mark as fully ready immediately
                    if is_small_model:
                        if not hasattr(self, 'preload_success_models'):
                            self.preload_success_models = set()
                        self.preload_success_models.add(model_name)
                        self.show_status_message(f"Small model '{model_name}' marked as ready based on 'ollama show'")
                    
                    return True
            except Exception as e:
                # Only log errors occasionally to avoid spam
                model_check_key = f"error_{model_name}"
                if model_check_key not in self._model_check_count or self._model_check_count[model_check_key] % 10 == 0:
                    self.show_status_message(f"Error checking model with 'ollama show': {str(e)}")
                    self._model_check_count[model_check_key] = self._model_check_count.get(model_check_key, 0) + 1
                pass
                
            return False
            
        except Exception:
            return False
    
    def fetch_model_info_async(self, model_name):
        """Fetch model information asynchronously after model is confirmed loaded."""
        def fetch_info():
            try:
                # Check if operation was cancelled before starting
                if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
                    getattr(self, 'current_loading_model', '') != model_name):
                    return
                
                # Extended delay for large models to ensure they're fully stabilized
                model_lower = model_name.lower()
                if any(size in model_lower for size in ['70b', '72b', '405b']):
                    time.sleep(3.0)  # 3 seconds for very large models
                elif any(size in model_lower for size in ['13b', '14b', '27b', '30b', '34b']):
                    time.sleep(2.0)  # 2 seconds for large models
                else:
                    time.sleep(1.0)  # 1 second for smaller models
                
                # Check again if operation was cancelled during delay
                if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
                    getattr(self, 'current_loading_model', '') != model_name):
                    return
                
                # Double-check that model is still loaded before getting details
                if not self.is_model_loaded_basic(model_name):
                    # Model disappeared, go back to loading state
                    if (not getattr(self, 'model_loading_cancelled', False) or 
                        getattr(self, 'current_loading_model', '') == model_name):
                        self.root.after(0, lambda: self.update_model_details_safe(model_name, loading=False))
                    return
                
                # Get detailed model information
                model_info = self.get_model_info(model_name)
                
                # Always try to display model info if we have any useful data
                # Even partial information is better than showing nothing
                if model_info:
                    # Final check before updating UI
                    if (not getattr(self, 'model_loading_cancelled', False) or 
                        getattr(self, 'current_loading_model', '') == model_name):
                        # Schedule UI update on main thread
                        self.root.after(0, lambda: self.update_model_info_display(model_name, model_info, loading=False))
                else:
                    # No model info at all, continue checking
                    if (not getattr(self, 'model_loading_cancelled', False) or 
                        getattr(self, 'current_loading_model', '') == model_name):
                        # Go back to checking if model is loaded
                        self.root.after(0, lambda: self.update_model_details_safe(model_name, loading=False))
                
            except Exception as e:
                # Only show error if operation wasn't cancelled
                if (not getattr(self, 'model_loading_cancelled', False) or 
                    getattr(self, 'current_loading_model', '') == model_name):
                    # Don't immediately show error - go back to loading state for large models
                    model_lower = model_name.lower()
                    if any(size in model_lower for size in ['70b', '72b', '405b', '13b', '14b', '27b', '30b', '34b']):
                        # For large models, retry the loading process
                        self.root.after(0, lambda: self.update_model_details_safe(model_name, loading=False))
                    else:
                        # For small models, show error
                        self.root.after(0, lambda: self.handle_model_info_error(model_name, str(e)))
        
        # Show intermediate loading status while we fetch detailed info
        # Only if operation wasn't cancelled
        if (not getattr(self, 'model_loading_cancelled', False) or 
            getattr(self, 'current_loading_model', '') == model_name):
            short_name = model_name.split(':')[0] if ':' in model_name else model_name
            self.model_status = "Loading"
            self.model_detail_lines[0].config(text="Model status: Loading", foreground="#1976D2")
            self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
        
        # Run in background thread to avoid blocking UI or user interactions
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def update_model_info_display(self, model_name, model_info, loading=False):
        """Update the UI with fetched model information."""
        # Check if operation was cancelled before updating UI
        if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
            getattr(self, 'current_loading_model', '') != model_name):
            return
            
        short_name = model_name.split(':')[0] if ':' in model_name else model_name
        
        # Check if model has passed the full inference verification via preload
        is_fully_verified = hasattr(self, 'preload_success_models') and model_name in self.preload_success_models
        
        # Check if we have valid model info - if so, display it and mark as ready
        has_valid_info = (model_info['size'] not in ["Unknown", "Error"] or 
                         model_info['ram_usage'] not in ["Unknown", "Error", "Not loaded"])
        
        # Show model details if we have any valid information OR if model is verified
        if is_fully_verified or has_valid_info:
            self.model_status = "Ready"
            
            # Enable chat input and send button when model is ready
            self.user_input.config(state='normal')
            self.send_button.config(state='normal')
            
            # Always display model information when we have it
            # Set color based on content - blue for loading/unknown, green for actual data
            size_color = "#1976D2" if model_info['size'] in ["Unknown", "Loading...", "Error"] else "green"
            ram_color = "#1976D2" if model_info['ram_usage'] in ["Unknown", "Loading...", "Error", "Not loaded"] else "green"
            usage_color = "#1976D2" if model_info['gpu_cpu_usage'] in ["Unknown", "Loading...", "Error"] else "green"
            context_color = "#1976D2" if model_info['context'] in ["Unknown", "Loading...", "Error"] else "green"
            
            # Update status line
            self.model_detail_lines[0].config(text="Model status: Ready", foreground="green")
            self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
            
            # Always show the detailed model information
            self.model_detail_lines[2].config(text=f"Model size: {model_info['size']}", foreground=size_color)
            self.model_detail_lines[3].config(text=f"RAM usage: {model_info['ram_usage']}", foreground=ram_color)
            self.model_detail_lines[4].config(text=f"CPU/GPU usage: {model_info['gpu_cpu_usage']}", foreground=usage_color)
            self.model_detail_lines[5].config(text=f"Context size: {model_info['context']}", foreground=context_color)
            
            # Extract and store max context tokens for token counter
            context_str = model_info['context']
            if context_str not in ["Unknown", "Loading...", "Error"]:
                try:
                    # Parse context size with K/M/B suffixes (e.g. "131K", "1.5M", "2B")
                    if "tokens" in context_str.lower():
                        # Old format with "tokens" suffix
                        self.max_context_tokens = int(context_str.lower().split("tokens")[0].strip())
                    else:
                        # New format with K/M/B suffixes
                        context_str = context_str.strip().upper()
                        if context_str.endswith('K'):
                            # e.g. "131K" -> 131000
                            self.max_context_tokens = int(float(context_str[:-1]) * 1000)
                        elif context_str.endswith('M'):
                            # e.g. "1.5M" -> 1500000
                            self.max_context_tokens = int(float(context_str[:-1]) * 1000000)
                        elif context_str.endswith('B'):
                            # e.g. "2B" -> 2000000000 (but this would be parameter count, not context)
                            self.max_context_tokens = int(float(context_str[:-1]) * 1000000000)
                        else:
                            # Plain number
                            self.max_context_tokens = int(''.join(c for c in context_str if c.isdigit()))
                except (ValueError, AttributeError):
                    self.max_context_tokens = 4096  # Default if parsing fails
            else:
                self.max_context_tokens = 4096  # Default fallback
                
            # Update token counter display
            self.update_token_counter()
            
            # Update chat display to show model is ready
            self.update_chat_for_ready_model(model_name)
            
            # Add model to success list if not already there
            if not hasattr(self, 'preload_success_models'):
                self.preload_success_models = set()
            self.preload_success_models.add(model_name)
        # Special case handling if we don't have good info yet
        # still mark as ready but show a note
        elif (not is_fully_verified and not loading and
              model_info['size'] not in ["Error", "Unknown"] and 
              model_info['ram_usage'] not in ["Error", "Unknown", "Not loaded"]):
            
            # For small models, be more lenient about readiness
            model_lower = model_name.lower()
            is_small_model = not any(size in model_lower for size in ['70b', '72b', '405b', '13b', '14b', '27b', '30b', '34b', '7b', '8b', '9b'])
            
            if is_small_model:
                self.model_status = "Ready"
                status_color = "green" 
                status_text = "Model status: Ready"
                
                # Enable chat for small models even with limited verification
                self.user_input.config(state='normal')
                self.send_button.config(state='normal')
                
                # Display model information
                # Set color based on content - blue for loading/unknown, green for actual data
                size_color = "#1976D2" if model_info['size'] in ["Unknown", "Loading...", "Error"] else "green"
                ram_color = "#1976D2" if model_info['ram_usage'] in ["Unknown", "Loading...", "Error", "Not loaded"] else "green"
                usage_color = "#1976D2" if model_info['gpu_cpu_usage'] in ["Unknown", "Loading...", "Error"] else "green"
                context_color = "#1976D2" if model_info['context'] in ["Unknown", "Loading...", "Error"] else "green"
                
                loading_note = self.get_loading_attempts_note(model_name)
                self.model_detail_lines[2].config(text=f"Model size: {model_info['size']}{loading_note}", foreground=size_color)
                self.model_detail_lines[3].config(text=f"RAM usage: {model_info['ram_usage']}", foreground=ram_color)
                self.model_detail_lines[4].config(text=f"CPU/GPU usage: {model_info['gpu_cpu_usage']}", foreground=usage_color)
                self.model_detail_lines[5].config(text=f"Context size: {model_info['context']}", foreground=context_color)
                
                # Extract and store max context tokens for token counter
                context_str = model_info['context']
                if context_str not in ["Unknown", "Loading...", "Error"]:
                    try:
                        # Parse context size with K/M/B suffixes (e.g. "131K", "1.5M", "2B")
                        if "tokens" in context_str.lower():
                            # Old format with "tokens" suffix
                            self.max_context_tokens = int(context_str.lower().split("tokens")[0].strip())
                        else:
                            # New format with K/M/B suffixes
                            context_str = context_str.strip().upper()
                            if context_str.endswith('K'):
                                # e.g. "131K" -> 131000
                                self.max_context_tokens = int(float(context_str[:-1]) * 1000)
                            elif context_str.endswith('M'):
                                # e.g. "1.5M" -> 1500000
                                self.max_context_tokens = int(float(context_str[:-1]) * 1000000)
                            elif context_str.endswith('B'):
                                # e.g. "2B" -> 2000000000 (but this would be parameter count, not context)
                                self.max_context_tokens = int(float(context_str[:-1]) * 1000000000)
                            else:
                                # Plain number
                                self.max_context_tokens = int(''.join(c for c in context_str if c.isdigit()))
                    except (ValueError, AttributeError):
                        self.max_context_tokens = 4096  # Default if parsing fails
                else:
                    self.max_context_tokens = 4096  # Default fallback
                    
                # Update token counter display
                self.update_token_counter()
                
                # Update chat display
                self.update_chat_for_ready_model(model_name)
                
                # Add to preload success list since we're treating it as ready
                if not hasattr(self, 'preload_success_models'):
                    self.preload_success_models = set()
                self.preload_success_models.add(model_name)
                
                self.show_status_message(f"Small model '{model_name}' marked as ready")
            else:
                # For larger models, still wait for full verification
                self.model_status = "Loading"
                status_color = "#1976D2"  # Blue
                status_text = "Model status: Loading"
                
                # Ensure chat input remains disabled during loading
                self.user_input.config(state='disabled')
                self.send_button.config(state='disabled')
        elif loading or not is_fully_verified:
            # If model is still loading or hasn't passed inference verification, keep the loading status
            self.model_status = "Loading"
            status_color = "#1976D2"  # Blue
            status_text = "Model status: Loading"
            
            # Ensure chat input remains disabled during loading
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
            
            # Show model data
            # Set color based on content - blue for loading/unknown, green for actual data
            size_color = "#1976D2" if model_info['size'] in ["Unknown", "Loading...", "Error"] else "green"
            ram_color = "#1976D2" if model_info['ram_usage'] in ["Unknown", "Loading...", "Error", "Not loaded"] else "green"
            usage_color = "#1976D2" if model_info['gpu_cpu_usage'] in ["Unknown", "Loading...", "Error"] else "green"
            context_color = "#1976D2" if model_info['context'] in ["Unknown", "Loading...", "Error"] else "green"
            
            loading_note = self.get_loading_attempts_note(model_name)
            self.model_detail_lines[2].config(text=f"Model size: {model_info['size']}{loading_note}", foreground=size_color)
            self.model_detail_lines[3].config(text=f"RAM usage: {model_info['ram_usage']}", foreground=ram_color)
            self.model_detail_lines[4].config(text=f"CPU/GPU usage: {model_info['gpu_cpu_usage']}", foreground=usage_color)
            self.model_detail_lines[5].config(text=f"Context size: {model_info['context']}", foreground=context_color)
            
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
        else:
            self.model_status = "Error"
            status_color = "red"
            status_text = "Model status: Error"
            
            # Keep chat disabled on error
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
            
            # Clear model data lines when not ready
            self.model_detail_lines[2].config(text="", foreground="green")
            self.model_detail_lines[3].config(text="", foreground="green") 
            self.model_detail_lines[4].config(text="", foreground="green")
            self.model_detail_lines[5].config(text="", foreground="green")
        
        # Update status and model name lines
        self.model_detail_lines[0].config(text=status_text, foreground=status_color)
        self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
    
    def handle_model_info_error(self, model_name, error_msg):
        """Handle errors when fetching model information."""
        # Check if operation was cancelled before showing error
        if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
            getattr(self, 'current_loading_model', '') != model_name):
            return
            
        short_name = model_name.split(':')[0] if ':' in model_name else model_name
        
        # Check if model is already in the verified loaded list despite the error
        if hasattr(self, 'preload_success_models') and model_name in self.preload_success_models:
            # Model is actually loaded, just having trouble getting details
            self.model_status = "Ready"
            self.model_detail_lines[0].config(text="Model status: Ready (with limited info)", foreground="green")
            self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
            
            # Enable chat since model is loaded
            self.user_input.config(state='normal')
            self.send_button.config(state='normal')
            
            # Set basic info
            self.model_detail_lines[2].config(text="Model size: Limited info", foreground="#1976D2")
            self.model_detail_lines[3].config(text="RAM usage: Limited info", foreground="#1976D2") 
            self.model_detail_lines[4].config(text="CPU/GPU usage: Limited info", foreground="#1976D2")
            self.model_detail_lines[5].config(text="Context size: Using default", foreground="#1976D2")
            
            # Update chat display to show model is ready
            self.update_chat_for_ready_model(model_name)
            
            # Log the issue but don't treat as error
            self.show_status_message(f"Note: Limited model info for '{model_name}' but chat is enabled: {error_msg}")
        else:
            # Try to preload the model instead of showing error
            self.show_status_message(f"Error getting model info: {error_msg}. Trying to initialize model...")
            
            # Keep UI in loading state
            self.model_status = "Loading"
            self.model_detail_lines[0].config(text="Model status: Loading (retrying...)", foreground="#1976D2")
            self.model_detail_lines[1].config(text=f"Selected model: {short_name}", foreground="green")
            
            # Keep chat disabled during loading
            self.user_input.config(state='disabled')
            self.send_button.config(state='disabled')
            
            # Set basic info while loading
            self.model_detail_lines[2].config(text="Model size: Loading...", foreground="#1976D2")
            self.model_detail_lines[3].config(text="RAM usage: Loading...", foreground="#1976D2")
            self.model_detail_lines[4].config(text="CPU/GPU usage: Loading...", foreground="#1976D2")
            self.model_detail_lines[5].config(text="Context size: Loading...", foreground="#1976D2")
            
            # Try to preload the model
            threading.Thread(target=self.preload_model_safe, args=(model_name,), daemon=True).start()

    def preload_model(self, model_name):
        """Pre-load the model to make it ready for immediate use."""
        try:
            # Check if operation was cancelled before starting
            if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
                getattr(self, 'current_loading_model', '') != model_name):
                return
                
            # Even if model shows as loaded in ps, we'll send a test query to ensure it's fully loaded
            # But first, show a message that we're checking/loading the model
            self.show_status_message(f"Preparing model '{model_name}' for use...")
            self.model_status = "Loading"
                
            # Set flag to indicate we're actively preloading this model
            self.preloading_model = True
            
            # Determine timeout based on model size - larger models need more time
            timeout = 45  # Increased default timeout for all models
            model_lower = model_name.lower()
            if any(size in model_lower for size in ['70b', '72b', '405b']):
                timeout = 180  # 3 minutes for very large models
            elif any(size in model_lower for size in ['13b', '14b', '27b', '30b', '34b']):
                timeout = 120  # 2 minutes for large models
            elif any(size in model_lower for size in ['7b', '8b', '9b']):
                timeout = 90   # 1.5 minutes for medium models
            
            # Check if this is a small model - special handling for faster loading
            is_small_model = not any(size in model_lower for size in ['70b', '72b', '405b', '13b', '14b', '27b', '30b', '34b', '7b', '8b', '9b'])
            
            # For slower machines or cold starts, we need to be more patient
            # Check if we need to try a different approach for loading
            is_first_attempt = not hasattr(self, '_model_load_attempts')
            if not is_first_attempt:
                if model_name not in self._model_load_attempts:
                    self._model_load_attempts[model_name] = 1
                else:
                    # Increase timeout for subsequent attempts
                    self._model_load_attempts[model_name] += 1
                    timeout = min(timeout * self._model_load_attempts[model_name], 300)  # Max 5 minutes
            else:
                self._model_load_attempts = {}
                self._model_load_attempts[model_name] = 1
                
            # Display loading attempts in status message for user awareness
            attempt_str = ""
            if self._model_load_attempts[model_name] > 1:
                attempt_str = f" (Attempt {self._model_load_attempts[model_name]})"
                
            # For small models, we'll use a quicker approach
            if is_small_model:
                self.root.after(0, lambda: self.show_status_message(f"Small model '{model_name}' detected, using optimized loading approach..."))
                # Don't need extended timeouts for small models
                timeout = min(timeout, 60)
            
            # Show loading status with timeout info for user awareness
            if timeout > 60:
                self.root.after(0, lambda: self.show_status_message(f"Loading model '{model_name}'{attempt_str} (may take up to {timeout//60} minute{'s' if timeout > 60 else ''}...)"))
            else:
                self.root.after(0, lambda: self.show_status_message(f"Loading model '{model_name}'{attempt_str} (may take up to {timeout} seconds)..."))
            
            # Try a simpler approach first for faster loading
            try:
                # First try with a simple ollama show to check if model is ready
                self.root.after(0, lambda: self.show_status_message(f"Checking if model '{model_name}' is already available..."))
                show_result = subprocess.run([self.ollama_path, "show", model_name], 
                                          capture_output=True, text=True, timeout=10)
                
                if show_result.returncode == 0 and show_result.stdout.strip():
                    # Model seems to be available, try a short warmup prompt
                    warmup_prompt = "hi"
                    self.root.after(0, lambda: self.show_status_message(f"Sending a quick test message to '{model_name}'..."))
                    
                    quick_result = subprocess.run([self.ollama_path, "run", model_name, warmup_prompt], 
                                              capture_output=True, text=True, timeout=30)
                    
                    if quick_result.returncode == 0:
                        # Model is ready without full initialization
                        self.root.after(0, lambda: self.show_status_message(f"✅ Model '{model_name}' is ready for use"))
                        # Set our variable and return early
                        self.preloaded_models[model_name] = time.time()
                        self.preload_success_models.add(model_name)
                        self.preloading_model = False
                        
                        # Get model info
                        model_info = self.get_model_info(model_name)
                        if model_info:
                            self.root.after(0, lambda: self.update_model_info_display(model_name, model_info, loading=False))
                            self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
                        return
            except Exception as e:
                # Continue with full initialization if quick check fails
                self.root.after(0, lambda: self.show_status_message(f"Quick check for '{model_name}' didn't work, proceeding with full initialization..."))
            
            # If we got here, the quick check didn't work - proceed with full initialization
            # We use a more substantial prompt to ensure the model is fully loaded and ready for inference
            warmup_prompt = "Please respond with a single word: 'Ready'. This query is to ensure you're fully loaded."
            
            self.root.after(0, lambda: self.show_status_message(f"Initializing model '{model_name}'... this ensures it's fully ready"))
            result = subprocess.run([self.ollama_path, "run", model_name, warmup_prompt], 
                                  capture_output=True, text=True, timeout=timeout)
            
            # Check if operation was cancelled during preload
            if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
                getattr(self, 'current_loading_model', '') != model_name):
                return
            
            # Consider success if ANY output was received, don't be too strict
            if result.returncode == 0:
                self.root.after(0, lambda: self.show_status_message(f"✅ Model '{model_name}' loaded successfully and ready for inference!"))
                # Reset preloading flag
                self.preloading_model = False
                
                # We know the model was successfully loaded because the command completed
                # Keep track of successfully preloaded models with timestamp
                if not hasattr(self, 'preloaded_models'):
                    self.preloaded_models = {}
                if not hasattr(self, 'preload_success_models'):
                    self.preload_success_models = set()
                self.preloaded_models[model_name] = time.time()
                self.preload_success_models.add(model_name)
                
                # Get the model info directly
                try:
                    model_info = self.get_model_info(model_name)
                    
                    # Add loading attempt info to model info
                    if hasattr(self, '_model_load_attempts') and model_name in self._model_load_attempts:
                        attempt_count = self._model_load_attempts[model_name]
                        if attempt_count > 1:  # Only show if there were multiple attempts
                            model_info['loading_note'] = f"(Loaded after {attempt_count} attempt{'s' if attempt_count > 1 else ''})"
                    
                    # Update UI only if we got meaningful model info and operation wasn't cancelled
                    if (model_info and model_info.get('ram_usage') not in ['Unknown', 'Error'] and 
                        (not getattr(self, 'model_loading_cancelled', False) or 
                         getattr(self, 'current_loading_model', '') == model_name)):
                        
                        # Enable chat input and update UI
                        self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
                        self.root.after(0, lambda: self.update_model_info_display(model_name, model_info))
                    else:
                        # If we couldn't get complete model info, still enable chat since we know model is loaded
                        self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
                except Exception as e:
                    # If there was an error getting model info, still enable chat since we know model is loaded
                    self.root.after(0, lambda: self.show_status_message(f"Note: Error getting model details, but model is loaded: {str(e)}"))
                    self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
            else:
                # For small models, sometimes the run command fails but the model is still usable
                # Try to check if it's at least accessible via 'ollama show' as a fallback
                try:
                    show_result = subprocess.run([self.ollama_path, "show", model_name], 
                                              capture_output=True, text=True, timeout=5)
                    
                    if show_result.returncode == 0 and show_result.stdout.strip():
                        # Model is at least detected by ollama show, mark as loaded with warning
                        self.root.after(0, lambda: self.show_status_message(f"⚠️ Model '{model_name}' loaded but with potential issues. Chat may still work."))
                        
                        # Still register it as available
                        if not hasattr(self, 'preloaded_models'):
                            self.preloaded_models = {}
                        if not hasattr(self, 'preload_success_models'):
                            self.preload_success_models = set()
                        self.preloaded_models[model_name] = time.time()
                        self.preload_success_models.add(model_name)
                        
                        # Enable chat despite warnings
                        self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
                    else:
                        # Model genuinely failed to load
                        self.root.after(0, lambda: self.show_status_message(f"⚠️ Could not initialize model '{model_name}'. Trying again..."))
                        # Try one more time with different approach
                        self.root.after(1000, lambda: self.update_model_details_safe(model_name, loading=True))
                except Exception as e:
                    self.root.after(0, lambda: self.show_status_message(f"⚠️ Model '{model_name}' check failed: {str(e)}"))
                
                # Reset preloading flag
                self.preloading_model = False
                
        except subprocess.TimeoutExpired:
            # Reset preloading flag but keep track of attempt
            self.preloading_model = False
            
            # Track timeout attempt
            if not hasattr(self, '_model_timeout_attempts'):
                self._model_timeout_attempts = {}
            
            if model_name not in self._model_timeout_attempts:
                self._model_timeout_attempts[model_name] = 1
            else:
                self._model_timeout_attempts[model_name] += 1
            
            # Check if we should still keep trying
            if self._model_timeout_attempts[model_name] <= 3:
                # Try alternate loading strategy on timeout
                if (not getattr(self, 'model_loading_cancelled', False) or 
                    getattr(self, 'current_loading_model', '') == model_name):
                    self.root.after(0, lambda: self.show_status_message(f"⏰ Model '{model_name}' loading timed out. Trying alternate loading method ({self._model_timeout_attempts[model_name]}/3)..."))
                    
                    # Try with simpler prompt approach
                    try:
                        # See if model is at least accessible via show
                        show_result = subprocess.run([self.ollama_path, "show", model_name], 
                                                  capture_output=True, text=True, timeout=10)
                        
                        if show_result.returncode == 0:
                            # Model exists, mark as loaded with warnings
                            self.root.after(0, lambda: self.show_status_message(f"Model '{model_name}' is available but loading timed out. Will proceed with limited functionality."))
                            
                            # Still register it as available
                            if not hasattr(self, 'preloaded_models'):
                                self.preloaded_models = {}
                            if not hasattr(self, 'preload_success_models'):
                                self.preload_success_models = set()
                            self.preloaded_models[model_name] = time.time()
                            self.preload_success_models.add(model_name)
                            
                            # Get model info and enable chat
                            model_info = self.get_model_info(model_name)
                            if model_info:
                                self.root.after(0, lambda: self.update_model_info_display(model_name, model_info))
                                self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
                    except Exception:
                        # If all else fails, retry with increased timeout
                        self.root.after(0, lambda: self.show_status_message(f"Retrying '{model_name}' load with increased timeout..."))
                        # Schedule a new attempt with increased timeout
                        self.root.after(1000, lambda: threading.Thread(
                            target=self.preload_model, 
                            args=(model_name,), 
                            daemon=True
                        ).start())
            else:
                # After multiple timeouts, try to make the best of it
                if (not getattr(self, 'model_loading_cancelled', False) or 
                    getattr(self, 'current_loading_model', '') == model_name):
                    self.root.after(0, lambda: self.show_status_message(f"⚠️ Model '{model_name}' keeps timing out. Will try to use it anyway with limited verification."))
                    
                    # Even after timeout, mark as potentially usable
                    if not hasattr(self, 'preloaded_models'):
                        self.preloaded_models = {}
                    self.preloaded_models[model_name] = time.time()
                    
                    # Don't add to preload_success_models to maintain accurate tracking
                    # But still try to update UI
                    self.root.after(0, lambda: self.update_model_details_safe(model_name, loading=False))
                    
        except Exception as e:
            # Reset preloading flag
            self.preloading_model = False
            
            # Only show error if operation wasn't cancelled
            if (not getattr(self, 'model_loading_cancelled', False) or 
                getattr(self, 'current_loading_model', '') == model_name):
                
                # More user-friendly error message based on error type
                if "timed out" in str(e).lower():
                    self.root.after(0, lambda: self.show_status_message(f"⏰ Model '{model_name}' is taking longer to load. Will try a different approach."))
                    
                    # Try with ollama show as a fallback
                    try:
                        show_result = subprocess.run([self.ollama_path, "show", model_name], 
                                                  capture_output=True, text=True, timeout=10)
                        
                        if show_result.returncode == 0:
                            # Model exists, mark as loaded with limited verification
                            self.root.after(0, lambda: self.show_status_message(f"Model '{model_name}' is available with limited functionality."))
                            
                            # Still register it as available
                            if not hasattr(self, 'preloaded_models'):
                                self.preloaded_models = {}
                            self.preloaded_models[model_name] = time.time()
                            
                            # Get model info and try to update UI
                            model_info = self.get_model_info(model_name)
                            if model_info:
                                # Add an indicator of loading attempts to the model info
                                attempt_count = 0
                                if hasattr(self, '_model_load_attempts') and model_name in self._model_load_attempts:
                                    attempt_count = self._model_load_attempts[model_name]
                                if attempt_count > 0:
                                    model_info['loading_note'] = f"(Loaded after {attempt_count} attempt{'s' if attempt_count > 1 else ''})"
                                
                                self.root.after(0, lambda: self.update_model_info_display(model_name, model_info))
                    except Exception:
                        pass
                else:
                    error_msg = str(e)
                    # Truncate error message if too long
                    if len(error_msg) > 100:
                        error_msg = error_msg[:97] + "..."
                    self.root.after(0, lambda: self.show_status_message(f"Error loading model: {error_msg}"))
                
                # Still try to update details even after error - model might be partially functional
                self.root.after(0, lambda: self.update_model_details_safe(model_name, loading=False))

    def show_status_message(self, message):
        """Show a status message in the logs display.
        
        Logs are kept clean and user-friendly, avoiding verbose technical details
        like PIDs, character counts, or debug output that clutter the interface.
        """
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
        
        # If we're currently loading a different model, cancel any pending operations
        if hasattr(self, 'model_loading_cancelled'):
            self.model_loading_cancelled = True
        
        # Set flags to track current model loading operation
        self.model_loading_cancelled = False
        self.current_loading_model = selected
        self.preloading_model = False  # Initialize the preloading flag
        
        # Reset model readiness tracking
        if not hasattr(self, 'preloaded_models'):
            self.preloaded_models = {}
        if not hasattr(self, 'preload_success_models'):
            self.preload_success_models = set()
        if not hasattr(self, 'preload_started_models'):
            self.preload_started_models = set()
            
        # Remove this model from preloaded tracking if it was there
        if selected in self.preloaded_models:
            del self.preloaded_models[selected]
        if selected in self.preload_success_models:
            self.preload_success_models.remove(selected)
        if selected in self.preload_started_models:
            self.preload_started_models.remove(selected)
        
        self.selected_model = selected
        
        # Save settings when model changes
        self.save_settings()
        
        # Reset conversation history for new model
        self.reset_conversation_history()
        
        # Immediately reset model state to prevent conflicts
        self.model_status = "Loading"
        
        # Show loading state immediately
        self.update_model_details(selected, loading=True)
        
        # Clear chat display and show loading message with time estimate
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        
        # Provide time estimate based on model size
        model_lower = selected.lower()
        time_estimate = ""
        if any(size in model_lower for size in ['70b', '72b', '405b']):
            time_estimate = " (Large model - may take 1-2 minutes)"
        elif any(size in model_lower for size in ['13b', '14b', '27b', '30b', '34b']):
            time_estimate = " (Large model - may take 60-90 seconds)"
        elif any(size in model_lower for size in ['7b', '8b', '9b']):
            time_estimate = " (May take up to 1 minute)"
        
        self.chat_display.insert(tk.END, f"⏳ Loading model '{selected}'{time_estimate}...\n")
        self.chat_display.insert(tk.END, "Please wait while the model is being prepared for use.\n")
        if time_estimate:
            self.chat_display.insert(tk.END, "Large models require more time to initialize.\n")
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state='disabled')
        
        # Clear input field while ensuring it stays disabled during loading
        # Temporarily enable to clear content, then immediately disable
        current_state = str(self.user_input.cget('state'))
        self.user_input.config(state='normal')
        self.user_input.delete("1.0", tk.END)
        self.user_input.config(state='disabled')  # Ensure it's disabled during loading
        
        # Keep send button disabled during loading
        self.send_button.config(state='disabled')
        
        # Pre-load the model and update details in background
        # Show appropriate loading message based on model size
        model_lower = selected.lower()
        if any(size in model_lower for size in ['70b', '72b', '405b']):
            self.show_status_message(f"Loading large model '{selected}' (may take 1-2 minutes)...")
        elif any(size in model_lower for size in ['13b', '14b', '27b', '30b', '34b']):
            self.show_status_message(f"Loading large model '{selected}' (may take 60-90 seconds)...")
        else:
            self.show_status_message(f"Loading model '{selected}'...")
        
        def load_model_info():
            # Keep track of which model this thread is processing
            current_model = selected
            
            # Check if model is already ready - avoid redundant processing
            if (hasattr(self, 'model_status') and self.model_status == "Ready" and 
                hasattr(self, 'selected_model') and self.selected_model == current_model):
                # Model is already ready - just make sure the UI reflects this
                self.root.after(0, lambda: self.enable_chat_for_loaded_model(current_model))
                return
            
            # Check if this operation was cancelled (user switched to another model)
            if getattr(self, 'model_loading_cancelled', False) or getattr(self, 'current_loading_model', '') != current_model:
                return
                
            # Small delay to make loading state visible
            time.sleep(0.2)
            
            # Check again if cancelled
            if getattr(self, 'model_loading_cancelled', False) or getattr(self, 'current_loading_model', '') != current_model:
                return
                
            # Check if the model is already loaded
            if self.is_model_loaded_basic(current_model):
                # Model is loaded according to basic check, but we need to verify it's fully ready
                self.root.after(0, lambda: self.show_status_message(f"Model '{current_model}' detected, verifying it's fully loaded..."))
                
                # Add to preload_started_models to track we've initiated the process
                if not hasattr(self, 'preload_started_models'):
                    self.preload_started_models = set()
                self.preload_started_models.add(current_model)
                
                # Update UI with detected status, but we won't enable chat until preload verification
                self.root.after(0, lambda: self.update_model_details_safe(current_model, loading=True))
                
                # Still run the preload process to verify it's fully loaded with inference
                # This will enable chat only when fully ready
                self.preload_model_safe(current_model)
            else:
                # Model is not loaded at all, preload it
                self.root.after(0, lambda: self.show_status_message(f"Model '{current_model}' not detected, starting load process..."))
                self.preload_model_safe(current_model)
                # No need to call update_model_details_safe here as preload_model will do that
                # if successful
        
        threading.Thread(target=load_model_info, daemon=True).start()
    
    def update_model_details_safe(self, model_name, loading=False):
        """Safe wrapper for update_model_details that checks for cancellation."""
        # Only proceed if this is still the current model being loaded
        if (not getattr(self, 'model_loading_cancelled', False) and 
            getattr(self, 'current_loading_model', '') == model_name):
            
            # Check if model is already marked as ready to avoid redundant checks
            if (hasattr(self, 'model_status') and self.model_status == "Ready" and
                hasattr(self, 'selected_model') and self.selected_model == model_name):
                # Model is already ready, no need to check status again
                return
                
            # Otherwise proceed with update
            self.update_model_details(model_name, loading=loading)
    
    def preload_model_safe(self, model_name):
        """Safe wrapper for preload_model that checks for cancellation."""
        # Only proceed if this is still the current model being loaded
        if (not getattr(self, 'model_loading_cancelled', False) and 
            getattr(self, 'current_loading_model', '') == model_name):
            
            # Check if model is already in process of preloading
            if getattr(self, 'preloading_model', False) and getattr(self, 'current_loading_model', '') == model_name:
                self.show_status_message(f"Model '{model_name}' is already being loaded, please wait...")
                # Update UI to show consistent loading status
                self.root.after(0, lambda: self.update_model_details(model_name, loading=True))
                return
            
            # Check if model is already fully verified loaded
            if hasattr(self, 'preload_success_models') and model_name in self.preload_success_models:
                self.show_status_message(f"Model '{model_name}' is already loaded and verified.")
                # Make sure UI shows the ready state
                model_info = self.get_model_info(model_name)
                if model_info:
                    self.root.after(0, lambda: self.update_model_info_display(model_name, model_info, loading=False))
                    self.root.after(0, lambda: self.enable_chat_for_loaded_model(model_name))
                return
                
            # Track that we've started preloading this model
            if not hasattr(self, 'preload_started_models'):
                self.preload_started_models = set()
            self.preload_started_models.add(model_name)
            
            # Make sure UI shows loading state
            self.root.after(0, lambda: self.update_model_details(model_name, loading=True))
            
            # Start preloading in a separate thread to avoid UI blocking
            threading.Thread(target=self.preload_model, args=(model_name,), daemon=True).start()
    
    def enable_chat_for_loaded_model(self, model_name):
        """Enable chat input when we know a model is loaded and ready for inference."""
        # Check if operation was cancelled
        if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
            getattr(self, 'current_loading_model', '') != model_name):
            return
            
        # Only enable if this is still the selected model
        if hasattr(self, 'selected_model') and self.selected_model == model_name:
            # Check if already in ready state to avoid redundant updates
            was_already_ready = (hasattr(self, 'model_status') and self.model_status == "Ready")
            
            # Check if the model is truly in the preloaded success list - this means
            # it passed our thorough testing with actual inference
            is_truly_ready = hasattr(self, 'preload_success_models') and model_name in self.preload_success_models
            
            # Only update status if model is truly ready or we're overriding due to a successful preload
            if is_truly_ready:
                # Set model as ready since we've confirmed it through inference
                self.model_status = "Ready"
                
                # Update UI status line
                self.model_detail_lines[0].config(text="Model status: Ready", foreground="green")
                
                # Enable chat input and send button immediately
                self.user_input.config(state='normal')
                self.send_button.config(state='normal')
                
                # Show a clear ready message if we're transitioning from loading
                if not was_already_ready:
                    self.show_status_message(f"✅ Model '{model_name}' is now fully ready for inference")
            
            # Only show message if this is the first time the model is marked as ready
            if not was_already_ready:
                self.show_status_message(f"Model '{model_name}' is ready for chat!")
                # Update chat display only the first time
                self.update_chat_for_ready_model(model_name)
    
    def update_chat_for_ready_model(self, model_name):
        """Update chat display when model is ready for use."""
        # Check if operation was cancelled or model switched
        if (hasattr(self, 'model_loading_cancelled') and self.model_loading_cancelled and 
            getattr(self, 'current_loading_model', '') != model_name):
            return
        
        # Verify model has passed the full inference check
        is_fully_verified = hasattr(self, 'preload_success_models') and model_name in self.preload_success_models
            
        # Only update if this is still the selected model and it's verified ready
        if (hasattr(self, 'selected_model') and self.selected_model == model_name and is_fully_verified):
            # Update chat display with ready message
            self.chat_display.config(state='normal')
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, f"✅ Model '{model_name}' is ready for chat!\n")
            self.chat_display.insert(tk.END, "💬 Type your message in the input field below and press Ctrl+Enter or click Send.\n\n")
            self.chat_display.config(state='disabled')
            
            # Focus on input field
            self.user_input.focus()

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
                
                # Handle stop message based on current mode
                if self.is_translator_mode:
                    # For translator mode, just show status message
                    self.finalize_translation_response()
                else:
                    # Add a message to the chat indicating the stop
                    self.chat_display.config(state='normal')
                    self.chat_display.insert(tk.END, "\n[Response stopped by user]\n\n")
                    self.chat_display.config(state='disabled')
                    self.chat_display.see(tk.END)
                    self.finalize_chat_response()
                
            except Exception as e:
                self.show_status_message(f"Error stopping generation: {str(e)}")
        
        # Reset state based on current mode
        if self.is_translator_mode:
            self.finalize_translation_response()
        else:
            self.finalize_chat_response()

    def on_input_keypress(self, event):
        """Handle key presses in the user input field."""
        # Don't process key events if input is disabled
        if str(self.user_input.cget('state')) == 'disabled':
            return "break"
            
        # Handle Ctrl+Enter - send message (Enter alone for new line)
        if event.keysym == "Return" and event.state & 0x4:  # 0x4 is Ctrl key
            # Send message
            self.send_message_from_input()
            return "break"
        
        # Allow normal text editing for Enter and other keys
        return None

    def on_translation_keypress(self, event):
        """Handle key presses in the translation input field."""
        # Handle Ctrl+Enter - start translation (Enter alone for new line)
        if event.keysym == "Return" and event.state & 0x4:  # 0x4 is Ctrl key
            # Check if translation is possible
            text = self.translation_input.get("1.0", tk.END).strip()
            if text and self.selected_model and not self.translation_in_progress:
                # Start translation
                self.translate_text()
                return "break"  # Prevent default action
            elif self.translation_in_progress:
                # Show message if translation is already in progress
                self.show_status_message("⚠️ Translation already in progress. Please wait or stop current translation.")
                return "break"
            elif not text:
                self.show_status_message("⚠️ Please enter text to translate.")
                return "break"
            elif not self.selected_model:
                self.show_status_message("⚠️ Please select a model first.")
                return "break"
        
        # Allow normal text editing for Enter and other keys
        return None

    def send_message_from_input(self):
        """Send message from the user input field."""
        if self.is_downloading:
            self.show_status_message("⚠️ Chat is disabled while downloading model. Please wait for download to complete.")
            return
            
        if self.is_translator_mode:
            self.show_status_message("⚠️ Chat is disabled in translator mode. Switch to Chat mode to send messages.")
            return
            
        if not self.selected_model:
            self.show_status_message("⚠️ Please choose a model first using the 'Choose Model' button.")
            return
        
        # Check model status before allowing message sending
        model_ready = False
        
        # First check if model was properly preloaded with inference verification
        if hasattr(self, 'preload_success_models') and self.selected_model in self.preload_success_models:
            model_ready = True
        
        # Next check UI status as fallback
        elif hasattr(self, 'model_status') and self.model_status == "Ready":
            model_ready = True
        
        # If UI says not ready, double-check if model is actually loaded
        if not model_ready:
            if self.is_model_loaded_basic(self.selected_model):
                # Model appears to be loaded but wasn't properly preloaded
                # Let's start preloading it properly and show message to user
                if not hasattr(self, 'preload_started_models'):
                    self.preload_started_models = set()
                
                if self.selected_model not in self.preload_started_models:
                    self.preload_started_models.add(self.selected_model)
                    self.show_status_message("⚠️ Model detected but not properly initialized. Starting initialization now...")
                    threading.Thread(target=self.preload_model_safe, args=(self.selected_model,)).start()
                    return
                else:
                    # We're already trying to preload it, continue with caution
                    self.enable_chat_for_loaded_model(self.selected_model)
                    model_ready = True
                    self.show_status_message("⚙️ Model is being initialized, but allowing chat to proceed...")
            else:
                # Model isn't actually loaded according to both checks
                if hasattr(self, 'model_status') and self.model_status == "Loading":
                    self.show_status_message("⚠️ Model is still loading. Please wait for the model to be ready.")
                elif hasattr(self, 'model_status') and self.model_status == "Error":
                    self.show_status_message("⚠️ Model has an error. Please try selecting the model again.")
                else:
                    self.show_status_message("⚠️ Please wait for the model to be ready before sending messages.")
                # Trigger a status refresh
                self.update_model_details_safe(self.selected_model, loading=False)
                return
        
        # Check if input field is disabled (shouldn't happen with proper UI state management)
        if str(self.user_input.cget('state')) == 'disabled':
            self.show_status_message("⚠️ Chat input is currently disabled. Please wait for model to be ready.")
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
                url = "http://localhost:11434/api/chat"  # Use chat API instead of generate API
                
                # Build messages array with conversation history (including the current user message)
                messages = []
                for message in self.conversation_history:
                    messages.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
                
                # Ensure we have at least one message (should not happen, but safety check)
                if not messages:
                    messages.append({
                        "role": "user",
                        "content": prompt
                    })
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {}
                }
                
                # Add model parameters to the payload
                if self.temperature_var.get() != 0.7:  # Only add if not default
                    payload["options"]["temperature"] = self.temperature_var.get()
                
                if self.top_p_var.get() != 0.9:  # Only add if not default
                    payload["options"]["top_p"] = self.top_p_var.get()
                
                if self.top_k_var.get() != 40:  # Only add if not default
                    payload["options"]["top_k"] = self.top_k_var.get()
                
                if self.repeat_penalty_var.get() != 1.1:  # Only add if not default
                    payload["options"]["repeat_penalty"] = self.repeat_penalty_var.get()
                
                if self.max_tokens_var.get() > 0:  # Only add if set
                    payload["options"]["num_predict"] = self.max_tokens_var.get()
                
                if self.seed_var.get() >= 0:  # Only add if not random (-1)
                    payload["options"]["seed"] = self.seed_var.get()
                
                # Remove options key if empty
                if not payload["options"]:
                    del payload["options"]
                
                # Store the request for potential cancellation
                self.current_request = requests.post(url, json=payload, stream=True, timeout=timeout)
                
                with self.current_request as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                # For chat API, the response content is in 'message.content'
                                chunk = data.get("message", {}).get("content", "")
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

    def get_default_settings(self):
        """Get default settings values."""
        return {
            # Model selection
            'selected_model': '',
            
            # Translation settings
            'source_language': 'English',
            'target_language': 'Spanish',
            'auto_detect_language': False,
            'translation_style': 'Natural',
            
            # Model parameters
            'response_timeout': '60',
            'show_thinking': False,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
            'max_tokens': 0,
            'seed': -1,
            
            # UI preferences
            'window_geometry': '1400x900',
            'mode': 'chat'  # Always starts in chat mode (not restored from settings)
        }
    
    def save_settings(self):
        """Save current settings to file."""
        try:
            settings = {
                # Model selection
                'selected_model': self.selected_model if self.selected_model else '',
                
                # Translation settings
                'source_language': self.source_lang_var.get(),
                'target_language': self.target_lang_var.get(),
                'auto_detect_language': self.auto_detect_var.get(),
                'translation_style': self.translation_style_var.get(),
                
                # Model parameters
                'response_timeout': self.response_timeout_var.get(),
                'show_thinking': self.show_thinking_var.get(),
                'temperature': self.temperature_var.get(),
                'top_p': self.top_p_var.get(),
                'top_k': self.top_k_var.get(),
                'repeat_penalty': self.repeat_penalty_var.get(),
                'max_tokens': self.max_tokens_var.get(),
                'seed': self.seed_var.get(),
                
                # UI preferences
                'window_geometry': self.root.geometry(),
                'mode': 'translator' if self.is_translator_mode else 'chat'
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            # Debug message (can be removed later)
            print(f"Settings saved to {self.settings_file}")
                
        except Exception as e:
            # Don't show error to user, just log it
            print(f"Error saving settings: {e}")
    
    def load_settings(self):
        """Load settings from file."""
        try:
            if not os.path.exists(self.settings_file):
                # No settings file exists, use defaults
                print("No settings file found, using defaults")
                return
                
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            print(f"Loading settings from {self.settings_file}")
            
            # Apply settings with fallbacks to defaults
            defaults = self.get_default_settings()
            
            # Translation settings
            self.source_lang_var.set(settings.get('source_language', defaults['source_language']))
            self.target_lang_var.set(settings.get('target_language', defaults['target_language']))
            self.auto_detect_var.set(settings.get('auto_detect_language', defaults['auto_detect_language']))
            self.translation_style_var.set(settings.get('translation_style', defaults['translation_style']))
            
            # Model parameters
            self.response_timeout_var.set(settings.get('response_timeout', defaults['response_timeout']))
            self.show_thinking_var.set(settings.get('show_thinking', defaults['show_thinking']))
            self.temperature_var.set(settings.get('temperature', defaults['temperature']))
            self.top_p_var.set(settings.get('top_p', defaults['top_p']))
            self.top_k_var.set(settings.get('top_k', defaults['top_k']))
            self.repeat_penalty_var.set(settings.get('repeat_penalty', defaults['repeat_penalty']))
            self.max_tokens_var.set(settings.get('max_tokens', defaults['max_tokens']))
            self.seed_var.set(settings.get('seed', defaults['seed']))
            
            # Window geometry
            window_geometry = settings.get('window_geometry', defaults['window_geometry'])
            if window_geometry:
                self.root.geometry(window_geometry)
            
            # Mode setting - Always start in Chat mode (don't restore saved mode)
            # saved_mode = settings.get('mode', defaults['mode'])
            # if saved_mode == 'translator':
            #     # Schedule mode switch after UI is ready
            #     self.root.after(100, self.switch_to_translator_mode)
            
            # Model selection - restore after models are loaded
            saved_model = settings.get('selected_model', '')
            if saved_model:
                # Schedule model restoration after models list is populated
                self.root.after(200, lambda: self.restore_selected_model(saved_model))
                
        except Exception as e:
            # Don't show error to user, just log it and continue with defaults
            print(f"Error loading settings: {e}")
    
    def restore_selected_model(self, model_name):
        """Restore previously selected model if it's still available."""
        try:
            if not model_name:
                return
                
            # Get current available models
            models = self.get_ollama_models()
            
            # Check if the saved model is still available
            if model_name in models:
                # Set the model in dropdown
                self.model_var.set(model_name)
                
                # Actually select the model (this will trigger loading)
                self.selected_model = model_name
                self.choose_model()
                
                self.show_status_message(f"✅ Restored previous model: {model_name}")
            else:
                # Model not available anymore
                if models:
                    self.show_status_message(f"⚠️ Previous model '{model_name}' not found. Available models refreshed.")
                else:
                    self.show_status_message(f"⚠️ Previous model '{model_name}' not found. No models available.")
                    
        except Exception as e:
            print(f"Error restoring model: {e}")

    def on_closing(self):
        """Handle application closing - cleanup processes."""
        try:
            # Save settings before closing
            self.save_settings()
            
            # Cancel any ongoing generation (chat or translation)
            if self.is_generating:
                self.is_generating = False
                if self.current_request:
                    self.current_request.close()
            
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
    
    def show_settings_dialog(self):
        """Show the model parameters settings dialog.
        
        This dialog allows users to configure:
        - Response timeout settings
        - Model reasoning display options
        - Model generation parameters (temperature, top_p, top_k, etc.)
        - Advanced settings (max tokens, seed)
        
        The dialog provides Apply, Cancel, and Default buttons:
        - Apply: Saves changes and logs them to system logs
        - Cancel: Discards changes and restores original values
        - Default: Resets all parameters to their default values
        """
        if not self.selected_model:
            messagebox.showwarning("No Model Selected", "Please select a model first to configure its parameters.")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Model Parameters - {self.selected_model.split(':')[0]}")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame with padding
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Parameters for {self.selected_model.split(':')[0]}", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Store original values for cancel functionality
        original_values = {
            'timeout': self.response_timeout_var.get(),
            'thinking': self.show_thinking_var.get(),
            'temperature': self.temperature_var.get(),
            'top_p': self.top_p_var.get(),
            'top_k': self.top_k_var.get(),
            'repeat_penalty': self.repeat_penalty_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'seed': self.seed_var.get()
        }
        
        # Create notebook for organized sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        # Response Timeout
        timeout_frame = ttk.LabelFrame(general_frame, text="Response Settings", padding=10)
        timeout_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(timeout_frame, text="Response Timeout (seconds):").pack(anchor='w')
        timeout_entry = ttk.Entry(timeout_frame, textvariable=self.response_timeout_var, width=10)
        timeout_entry.pack(anchor='w', pady=(5, 0))
        ttk.Label(timeout_frame, text="How long to wait for model response", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w', pady=(2, 0))
        
        # Show thinking toggle
        thinking_frame = ttk.LabelFrame(general_frame, text="Display Options", padding=10)
        thinking_frame.pack(fill=tk.X, pady=(0, 10))
        
        thinking_check = ttk.Checkbutton(thinking_frame, text="Show model reasoning (<think> tags)", 
                                        variable=self.show_thinking_var)
        thinking_check.pack(anchor='w')
        ttk.Label(thinking_frame, text="Display internal model reasoning when available", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w', pady=(2, 0))
        
        # Model parameters tab
        params_frame = ttk.Frame(notebook)
        notebook.add(params_frame, text="Model Parameters")
        
        # Temperature
        temp_frame = ttk.LabelFrame(params_frame, text="Temperature", padding=10)
        temp_frame.pack(fill=tk.X, pady=(0, 10))
        
        temp_scale = ttk.Scale(temp_frame, from_=0.1, to=2.0, variable=self.temperature_var, 
                              orient=tk.HORIZONTAL, length=300)
        temp_scale.pack(fill=tk.X)
        temp_value_label = ttk.Label(temp_frame, text="")
        temp_value_label.pack(anchor='w')
        ttk.Label(temp_frame, text="Controls randomness: lower = more focused, higher = more creative", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w')
        
        # Top P
        top_p_frame = ttk.LabelFrame(params_frame, text="Top P (Nucleus Sampling)", padding=10)
        top_p_frame.pack(fill=tk.X, pady=(0, 10))
        
        top_p_scale = ttk.Scale(top_p_frame, from_=0.1, to=1.0, variable=self.top_p_var, 
                               orient=tk.HORIZONTAL, length=300)
        top_p_scale.pack(fill=tk.X)
        top_p_value_label = ttk.Label(top_p_frame, text="")
        top_p_value_label.pack(anchor='w')
        ttk.Label(top_p_frame, text="Limits token choices to top probability mass", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w')
        
        # Top K
        top_k_frame = ttk.LabelFrame(params_frame, text="Top K", padding=10)
        top_k_frame.pack(fill=tk.X, pady=(0, 10))
        
        top_k_scale = ttk.Scale(top_k_frame, from_=1, to=100, variable=self.top_k_var, 
                               orient=tk.HORIZONTAL, length=300)
        top_k_scale.pack(fill=tk.X)
        top_k_value_label = ttk.Label(top_k_frame, text="")
        top_k_value_label.pack(anchor='w')
        ttk.Label(top_k_frame, text="Limits choices to top K most likely tokens", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w')
        
        # Repeat Penalty
        repeat_frame = ttk.LabelFrame(params_frame, text="Repeat Penalty", padding=10)
        repeat_frame.pack(fill=tk.X, pady=(0, 10))
        
        repeat_scale = ttk.Scale(repeat_frame, from_=0.5, to=2.0, variable=self.repeat_penalty_var, 
                                orient=tk.HORIZONTAL, length=300)
        repeat_scale.pack(fill=tk.X)
        repeat_value_label = ttk.Label(repeat_frame, text="")
        repeat_value_label.pack(anchor='w')
        ttk.Label(repeat_frame, text="Reduces repetition: higher values = less repetition", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w')
        
        # Advanced tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        # Max Tokens
        max_tokens_frame = ttk.LabelFrame(advanced_frame, text="Max Tokens", padding=10)
        max_tokens_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(max_tokens_frame, text="Maximum tokens to generate (0 = no limit):").pack(anchor='w')
        max_tokens_spinbox = ttk.Spinbox(max_tokens_frame, from_=0, to=4096, 
                                        textvariable=self.max_tokens_var, width=10)
        max_tokens_spinbox.pack(anchor='w', pady=(5, 0))
        ttk.Label(max_tokens_frame, text="Limits the length of model responses", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w', pady=(2, 0))
        
        # Seed
        seed_frame = ttk.LabelFrame(advanced_frame, text="Seed", padding=10)
        seed_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(seed_frame, text="Random seed (-1 = random):").pack(anchor='w')
        seed_spinbox = ttk.Spinbox(seed_frame, from_=-1, to=999999, 
                                  textvariable=self.seed_var, width=10)
        seed_spinbox.pack(anchor='w', pady=(5, 0))
        ttk.Label(seed_frame, text="Use same seed for reproducible outputs", 
                 font=('Arial', 9), foreground='#666').pack(anchor='w', pady=(2, 0))
        
        # Update value labels
        def update_value_labels():
            temp_value_label.config(text=f"Current: {self.temperature_var.get():.2f}")
            top_p_value_label.config(text=f"Current: {self.top_p_var.get():.2f}")
            top_k_value_label.config(text=f"Current: {int(self.top_k_var.get())}")
            repeat_value_label.config(text=f"Current: {self.repeat_penalty_var.get():.2f}")
        
        # Bind scale updates
        temp_scale.configure(command=lambda v: update_value_labels())
        top_p_scale.configure(command=lambda v: update_value_labels())
        top_k_scale.configure(command=lambda v: update_value_labels())
        repeat_scale.configure(command=lambda v: update_value_labels())
        
        # Initial value update
        update_value_labels()
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def apply_settings():
            """Apply current settings and close dialog."""
            try:
                # Validate timeout
                timeout_val = int(self.response_timeout_var.get())
                if timeout_val <= 0:
                    raise ValueError("Timeout must be positive")
                
                # Log settings changes
                self.show_status_message("✅ Model parameters applied successfully")
                
                # Log specific changes
                changes = []
                if original_values['temperature'] != self.temperature_var.get():
                    changes.append(f"Temperature: {original_values['temperature']:.2f} → {self.temperature_var.get():.2f}")
                if original_values['top_p'] != self.top_p_var.get():
                    changes.append(f"Top-P: {original_values['top_p']:.2f} → {self.top_p_var.get():.2f}")
                if original_values['top_k'] != self.top_k_var.get():
                    changes.append(f"Top-K: {original_values['top_k']} → {self.top_k_var.get()}")
                if original_values['repeat_penalty'] != self.repeat_penalty_var.get():
                    changes.append(f"Repeat penalty: {original_values['repeat_penalty']:.2f} → {self.repeat_penalty_var.get():.2f}")
                if original_values['max_tokens'] != self.max_tokens_var.get():
                    changes.append(f"Max tokens: {original_values['max_tokens']} → {self.max_tokens_var.get()}")
                if original_values['seed'] != self.seed_var.get():
                    changes.append(f"Seed: {original_values['seed']} → {self.seed_var.get()}")
                if original_values['timeout'] != self.response_timeout_var.get():
                    changes.append(f"Timeout: {original_values['timeout']}s → {self.response_timeout_var.get()}s")
                if original_values['thinking'] != self.show_thinking_var.get():
                    thinking_status = "enabled" if self.show_thinking_var.get() else "disabled"
                    changes.append(f"Show reasoning: {thinking_status}")
                
                if changes:
                    self.show_status_message(f"Parameter changes: {'; '.join(changes)}")
                else:
                    self.show_status_message("No parameter changes made")
                
                # Save settings after applying changes
                self.save_settings()
                
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Please check your input values:\n{str(e)}")
        
        def cancel_settings():
            """Cancel changes and restore original values."""
            self.response_timeout_var.set(original_values['timeout'])
            self.show_thinking_var.set(original_values['thinking'])
            self.temperature_var.set(original_values['temperature'])
            self.top_p_var.set(original_values['top_p'])
            self.top_k_var.set(original_values['top_k'])
            self.repeat_penalty_var.set(original_values['repeat_penalty'])
            self.max_tokens_var.set(original_values['max_tokens'])
            self.seed_var.set(original_values['seed'])
            
            self.show_status_message("Settings cancelled - original values restored")
            dialog.destroy()
        
        def default_settings():
            """Reset all settings to default values."""
            self.response_timeout_var.set("60")
            self.show_thinking_var.set(False)
            self.temperature_var.set(0.7)
            self.top_p_var.set(0.9)
            self.top_k_var.set(40)
            self.repeat_penalty_var.set(1.1)
            self.max_tokens_var.set(0)
            self.seed_var.set(-1)
            
            update_value_labels()
            self.show_status_message("All parameters reset to default values")
            dialog.destroy()
        
        # Buttons
        ttk.Button(button_frame, text="Apply", command=apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Default", command=default_settings).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Handle dialog close
        dialog.protocol("WM_DELETE_WINDOW", cancel_settings)
        
        # Focus on dialog
        dialog.focus_set()
    
    def get_language_list(self):
        """Return a list of supported languages for translation."""
        return [
            "English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian",
            "Chinese (Simplified)", "Chinese (Traditional)", "Japanese", "Korean", "Arabic",
            "Hindi", "Turkish", "Dutch", "Swedish", "Norwegian", "Danish", "Finnish",
            "Polish", "Czech", "Hungarian", "Romanian", "Bulgarian", "Croatian", "Serbian",
            "Greek", "Hebrew", "Thai", "Vietnamese", "Indonesian", "Malay", "Filipino",
            "Ukrainian", "Persian", "Urdu", "Bengali", "Tamil", "Telugu", "Marathi",
            "Gujarati", "Punjabi", "Nepali", "Sinhala", "Myanmar", "Khmer", "Lao",
            "Mongolian", "Kazakh", "Uzbek", "Azerbaijani", "Georgian", "Armenian",
            "Basque", "Catalan", "Galician", "Irish", "Welsh", "Scots Gaelic",
            "Icelandic", "Estonian", "Latvian", "Lithuanian", "Slovenian", "Slovak",
            "Macedonian", "Albanian", "Maltese", "Luxembourgish", "Afrikaans",
            "Swahili", "Zulu", "Xhosa", "Yoruba", "Igbo", "Hausa", "Amharic", "Somali"
        ]

    def update_mode_buttons(self):
        """Update the appearance of mode buttons based on current mode."""
        if self.is_translator_mode:
            self.chat_button.config(text="💬 Chat")
            self.translator_button.config(text="🌐 Translator ✓")
            self.root.title("Tkinter GUI for Ollama - Translator Mode")
        else:
            self.chat_button.config(text="💬 Chat ✓")
            self.translator_button.config(text="🌐 Translator")
            self.root.title("Tkinter GUI for Ollama - Chat Mode")
    
    def switch_to_chat_mode(self):
        """Switch to chat mode."""
        if self.is_translator_mode:
            self.is_translator_mode = False
            
            # Hide translator interface, show chat interface
            self.translator_interface.pack_forget()
            self.chat_interface.pack(fill=tk.BOTH, expand=True)
            
            # Disable translator settings frame (but keep it visible)
            self.set_translation_settings_state('disabled')
            
            # Update button appearance
            self.update_mode_buttons()
            
            # Save settings
            self.save_settings()
            
            self.show_status_message("Switched to Chat mode")
    
    def switch_to_translator_mode(self):
        """Switch to translator mode."""
        if not self.selected_model:
            messagebox.showwarning("No Model Selected", "Please select a model first before using the translator.")
            return
            
        if not self.is_translator_mode:
            self.is_translator_mode = True
            
            # Hide chat interface, show translator interface
            self.chat_interface.pack_forget()
            self.translator_interface.pack(fill=tk.BOTH, expand=True)
            
            # Enable translator settings frame
            self.set_translation_settings_state('normal')
            
            # Update button appearance
            self.update_mode_buttons()
            
            # Focus on translation input
            self.translation_input.focus()
            
            # Save settings
            self.save_settings()
            
            self.show_status_message("Switched to Translator mode")
    
    def set_translation_settings_state(self, state):
        """Enable or disable all translation settings widgets."""
        for widget in self.translation_widgets:
            widget.config(state=state)
        
        # Also update the labels to show visual feedback
        if state == 'disabled':
            # Make labels appear dimmed in chat mode
            self.from_label.config(foreground='gray')
            self.to_label.config(foreground='gray')
            self.style_label.config(foreground='gray')
            self.translator_frame.config(text="Translation Settings (Chat Mode)")
        else:
            # Restore normal appearance in translator mode
            self.from_label.config(foreground='black')
            self.to_label.config(foreground='black')  
            self.style_label.config(foreground='black')
            self.translator_frame.config(text="Translation Settings")
    
    def swap_languages(self):
        """Swap source and target languages."""
        if not self.auto_detect_var.get():  # Only swap if auto-detect is off
            source = self.source_lang_var.get()
            target = self.target_lang_var.get()
            self.source_lang_var.set(target)
            self.target_lang_var.set(source)
            
            # Save settings after swapping languages
            self.save_settings()
            
            self.show_status_message(f"Swapped languages: {target} ⇄ {source}")
    
    def on_translation_input_change(self, event=None):
        """Handle changes in translation input text."""
        text = self.translation_input.get("1.0", tk.END).strip()
        if text and self.selected_model:
            self.translate_button.config(state='normal')
        else:
            self.translate_button.config(state='disabled')
    
    def clear_translation(self):
        """Clear both input and output translation areas."""
        self.translation_input.delete("1.0", tk.END)
        self.translation_output.config(state='normal')
        self.translation_output.delete("1.0", tk.END)
        self.translation_output.config(state='disabled')
        self.translate_button.config(state='disabled')
        self.copy_translation_button.config(state='disabled')
        self.show_status_message("Translation areas cleared")
    
    def copy_translation_result(self):
        """Copy the translation result to clipboard."""
        result = self.translation_output.get("1.0", tk.END).strip()
        if result:
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            self.show_status_message("Translation copied to clipboard")
        else:
            self.show_status_message("No translation to copy")
    
    def translate_text(self):
        """Translate the text using the selected model."""
        if not self.selected_model:
            messagebox.showwarning("No Model Selected", "Please select a model first.")
            return
        
        if self.is_generating or self.translation_in_progress:
            self.show_status_message("⚠️ Please wait for current operation to complete")
            return
        
        text_to_translate = self.translation_input.get("1.0", tk.END).strip()
        if not text_to_translate:
            self.show_status_message("⚠️ Please enter text to translate")
            return
        
        # Get language settings
        source_lang = "auto-detect" if self.auto_detect_var.get() else self.source_lang_var.get()
        target_lang = self.target_lang_var.get()
        translation_style = self.translation_style_var.get().lower()
        
        # Create translation prompt based on your suggestion
        if self.auto_detect_var.get():
            prompt = f"Please translate the following text into {target_lang} in a {translation_style} style, without any explanation or additional text. Only provide the translation:\n\n{text_to_translate}"
        else:
            prompt = f"Please translate from {source_lang} into {target_lang} the following text in a {translation_style} style, without any explanation or additional text. Only provide the translation:\n\n{text_to_translate}"
        
        # Update UI state
        self.translation_in_progress = True
        self.is_generating = True
        self.translate_button.config(state='disabled')
        self.translation_stop_button.config(state='normal')
        
        # Clear previous result
        self.translation_output.config(state='normal')
        self.translation_output.delete("1.0", tk.END)
        self.translation_output.config(state='disabled')
        
        # Reset response accumulator
        self.current_response = ""
        
        self.show_status_message(f"Translating from {source_lang} to {target_lang}...")
        
        def run_translation():
            self.run_translation_query(self.selected_model, prompt)
        
        threading.Thread(target=run_translation, daemon=True).start()
    
    def run_translation_query(self, model, prompt):
        """Run translation query and update translator interface."""
        if not self.ollama_path:
            self.root.after(0, lambda: self.update_translation_output("Error: Ollama not found\n"))
            self.root.after(0, self.finalize_translation_response)
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
                    "stream": True,
                    "options": {}
                }
                
                # Add model parameters to the payload (same as chat)
                if self.temperature_var.get() != 0.7:
                    payload["options"]["temperature"] = self.temperature_var.get()
                
                if self.top_p_var.get() != 0.9:
                    payload["options"]["top_p"] = self.top_p_var.get()
                
                if self.top_k_var.get() != 40:
                    payload["options"]["top_k"] = self.top_k_var.get()
                
                if self.repeat_penalty_var.get() != 1.1:
                    payload["options"]["repeat_penalty"] = self.repeat_penalty_var.get()
                
                if self.max_tokens_var.get() > 0:
                    payload["options"]["num_predict"] = self.max_tokens_var.get()
                
                if self.seed_var.get() >= 0:
                    payload["options"]["seed"] = self.seed_var.get()
                
                # Remove options key if empty
                if not payload["options"]:
                    del payload["options"]
                
                # Store the request for potential cancellation
                self.current_request = requests.post(url, json=payload, stream=True, timeout=timeout)
                
                with self.current_request as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if 'response' in data:
                                    chunk = data['response']
                                    if chunk:
                                        self.current_response += chunk
                                        self.root.after(0, lambda c=chunk: self.update_translation_output(c))
                                
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                
                self.root.after(0, self.finalize_translation_response)
            except requests.exceptions.Timeout:
                self.root.after(0, lambda: self.update_translation_output("\nError: Request timed out.\n"))
                self.root.after(0, self.finalize_translation_response)
            except requests.exceptions.RequestException as e:
                if not self.is_generating:
                    return  # User stopped the generation
                self.root.after(0, lambda: self.update_translation_output(f"\nError: {str(e)}\n"))
                self.root.after(0, self.finalize_translation_response)
            except Exception as e:
                if not self.is_generating:
                    return  # User stopped the generation
                self.root.after(0, lambda: self.update_translation_output(f"\nAn unexpected error occurred: {str(e)}\n"))
                self.root.after(0, self.finalize_translation_response)
            finally:
                self.current_request = None

        threading.Thread(target=query, daemon=True).start()
    
    def update_translation_output(self, chunk):
        """Update the translation output with a chunk of text."""
        self.translation_output.config(state='normal')
        self.translation_output.insert(tk.END, chunk)
        self.translation_output.config(state='disabled')
        self.translation_output.see(tk.END)
    
    def finalize_translation_response(self):
        """Finalize the translation response and reset UI state."""
        # Apply thinking filter if needed
        if not self.show_thinking_var.get() and self.current_response:
            filtered_response = self.filter_thinking_tags(self.current_response)
            
            # Update the output with filtered response
            self.translation_output.config(state='normal')
            self.translation_output.delete("1.0", tk.END)
            self.translation_output.insert("1.0", filtered_response.strip())
            self.translation_output.config(state='disabled')
        
        # Reset UI state
        self.translation_in_progress = False
        self.is_generating = False
        self.current_request = None
        self.translate_button.config(state='normal')
        self.translation_stop_button.config(state='disabled')
        
        # Enable copy button if there's content
        result = self.translation_output.get("1.0", tk.END).strip()
        if result:
            self.copy_translation_button.config(state='normal')
            self.show_status_message("✅ Translation completed")
        else:
            self.copy_translation_button.config(state='disabled')
            self.show_status_message("⚠️ Translation completed but no result")
        
        # Focus back on input for next translation
        self.translation_input.focus()
    
if __name__ == "__main__":
    import re
    import random

    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()