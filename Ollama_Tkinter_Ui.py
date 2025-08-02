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
        """Show installation guide for Ollama in logs."""
        self.logs_display.delete(1.0, tk.END)
        guide = """>>> OLLAMA INSTALLATION GUIDE <<<

To install Ollama on Linux:

1. Download and install Ollama:
   curl -fsSL https://ollama.ai/install.sh | sh

2. Or install manually:
   - Visit https://ollama.ai/download/linux
   - Download the appropriate package for your system
   - Install using your package manager

3. After installation, you can:
   - Pull models: ollama pull llama3
   - Start server: ollama serve
   - List models: ollama list

4. Popular models to try:
   - ollama pull llama3
   - ollama pull mistral
   - ollama pull codellama
   - ollama pull phi3

5. Once installed, click 'Refresh' to detect models.

>>> Visit https://ollama.ai for more information <<<
"""
        self.logs_display.insert(tk.END, guide)

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
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.insert(tk.END, f"✅ Model '{selected}' is ready for chat!\n")
        self.chat_display.insert(tk.END, "📝 Type your message after the >>> prompt and press Enter or click Send.\n\n")
        self.setup_user_input_prompt()

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