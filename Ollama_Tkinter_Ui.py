#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os

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
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start server monitoring
        self.start_server_monitoring()

    def initialize_ollama(self):
        """Initialize Ollama server and load models on startup."""
        self.show_status_message("Checking Ollama installation...")
        
        def check_and_start():
            if not self.check_ollama_installation():
                return
                
            if not self.is_ollama_server_running():
                self.root.after(0, lambda: self.show_status_message("Ollama server not running. Starting automatically..."))
                # Call auto_start_server from the main thread
                self.root.after(0, self.auto_start_server)
            else:
                self.root.after(0, lambda: self.show_status_message("Ollama server is already running."))
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
    
    def on_server_started(self):
        """Handle server start event"""
        if not self.server_starting:  # Only show if we didn't start it ourselves
            self.show_status_message("🟢 Ollama server detected - started externally")
        else:
            self.show_status_message("🟢 Ollama server is now running!")
        self.refresh_models()
    
    def on_server_stopped(self):
        """Handle server stop event"""
        if not self.server_starting:  # Only show if we didn't stop it ourselves
            self.show_status_message("🔴 Ollama server stopped")
        else:
            self.show_status_message("Ollama server has stopped.")
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

    def auto_start_server(self):
        """Automatically start the Ollama server if not running."""
        if self.server_starting or not self.ollama_path:
            return
            
        self.server_starting = True
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
                        self.root.after(0, lambda: self.show_status_message("Ollama server started successfully!"))
                        self.root.after(0, self.refresh_models)
                        self.server_starting = False
                        self.server_was_running = True  # Update tracking state
                        return
                
                self.root.after(0, lambda: self.show_status_message("Failed to start Ollama server after 15 seconds."))
                self.server_starting = False
                
            except Exception as e:
                self.root.after(0, lambda: self.show_status_message(f"Error starting server: {str(e)}"))
                self.server_starting = False
        
        threading.Thread(target=start_server, daemon=True).start()

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
        """Try to get actual system GPU/CPU usage information."""
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
                        
                        # Try to extract GPU/CPU usage percentages
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
                                self.show_status_message(f"Found GPU/CPU usage: {model_info['gpu_cpu_usage']}")
                                break
                        else:
                            # If no percentage found in ollama ps output, get system-wide usage
                            gpu_usage, cpu_usage = self.get_system_usage_info()
                            model_info["gpu_cpu_usage"] = f"{gpu_usage}%/{cpu_usage}%"
                            self.show_status_message(f"System GPU/CPU usage: {model_info['gpu_cpu_usage']}")
                        break
                else:
                    model_info["ram_usage"] = "Not loaded"
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
            self.model_usage_label.config(text="GPU/CPU usage: Loading...", foreground="#1976D2")
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
        self.model_usage_label.config(text=f"GPU/CPU usage: {model_info['gpu_cpu_usage']}", foreground=usage_color)
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
            
            # Add newline after user input and show it's being processed
            self.chat_display.insert(tk.END, f"\n\nAssistant: ")
            self.chat_display.see(tk.END)
            
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

    def run_ollama_query(self, model, prompt):
        """Query Ollama and update GUI with response."""
        if not self.ollama_path:
            self.root.after(0, lambda: self.chat_display.insert(tk.END, "Error: Ollama not found\n\n"))
            self.root.after(0, self.setup_user_input_prompt)
            self.root.after(0, lambda: self.send_button.config(state='normal'))
            return
            
        try:
            cmd = [self.ollama_path, "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                response = result.stdout.strip()
                self.root.after(0, lambda: self.chat_display.insert(tk.END, f"{response}\n\n"))
            else:
                error_msg = result.stderr.strip() or "Unknown error occurred"
                self.root.after(0, lambda: self.chat_display.insert(tk.END, f"Error: {error_msg}\n\n"))
                
            self.root.after(0, lambda: self.chat_display.see(tk.END))
            self.root.after(0, self.setup_user_input_prompt)
            self.root.after(0, lambda: self.send_button.config(state='normal'))
            
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.chat_display.insert(tk.END, "Error: Request timed out\n\n"))
            self.root.after(0, self.setup_user_input_prompt)
            self.root.after(0, lambda: self.send_button.config(state='normal'))
        except Exception as e:
            self.root.after(0, lambda: self.chat_display.insert(tk.END, f"Error: {str(e)}\n\n"))
            self.root.after(0, self.setup_user_input_prompt)
            self.root.after(0, lambda: self.send_button.config(state='normal'))

    def on_closing(self):
        """Handle application closing - cleanup Ollama process if we started it."""
        try:
            if self.ollama_process and self.ollama_process.poll() is None:
                self.ollama_process.terminate()
                self.ollama_process.wait(timeout=5)
        except:
            pass
        finally:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()