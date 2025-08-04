# Ollama Tkinter GUI

A **simple and convenient** Python-based graphical user interface for [Ollama](https://ollama.ai), providing essential CLI functionality through an intuitive desktop application.

## 🚀 Overview

This is an extremely simple yet powerful GUI wrapper for Ollama that makes it easy to:
- **Automatically manage** the Ollama server (starts/stops as needed)
- **Browse and select** installed models
- **Download new models** with progress tracking
- **Chat interactively** with your chosen AI models
- **Monitor system resources** and model information
- **View detailed logs** of all operations

Perfect for users who want the convenience of a desktop interface without the complexity of command-line operations.

## ✨ Features

### 🤖 **Model Management**
- **Auto-discovery** of installed Ollama models
- **One-click model selection** with detailed information display
- **Model downloading** with real-time progress tracking and cancellation
- **Model information** showing size, RAM usage, GPU/CPU utilization, and context window

### 💬 **Interactive Chat**
- **Real-time chat** with selected AI models
- **Enter key support** for quick message sending
- **Clean chat interface** with proper message formatting
- **Automatic model loading** and status feedback

### 🔧 **Smart Server Management**
- **Automatic server startup** - no manual `ollama serve` needed
- **Intelligent server detection** - knows if server was started by system or user
- **Server restart functionality** - easily restart server in user context
- **Background server monitoring** with real-time status updates
- **Graceful shutdown** handling with process cleanup
- **Path auto-detection** for various Ollama installations

### 📊 **Advanced System Monitoring**
- **Server status indicator** - shows if started by system or user with color coding
- **Real-time system logs** showing all operations with detailed process information
- **Model resource usage** (RAM, GPU/CPU percentages)
- **Download progress tracking** with blue status indicators
- **Loading states** for all operations

### 🎨 **Professional User Experience**
- **Two-panel layout** (350px controls + expandable chat)
- **Server status section** with restart button for easy server management
- **Professional UI** with 1400x900 window size
- **Modal dialogs** for downloads and installation guides
- **Keyboard shortcuts** (Enter to send, Escape to cancel)
- **Built-in installation guide** accessible from Help menu

## 🛠️ Requirements

- **Python 3.6+** with tkinter (usually included)
- **Ollama** installed on your system
- **Linux/Unix environment** (tested on Linux)

### Optional Dependencies
- `psutil` - for more accurate CPU usage monitoring
- `nvidia-smi` - for GPU usage detection (if NVIDIA GPU available)

## 📦 Installation

1. **Install Ollama** (if not already installed):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Download the GUI**:
   ```bash
   wget https://github.com/avsDeveloper/OllamaTkinterUi/raw/main/Ollama_Tkinter_Ui.py
   # OR clone the repository
   git clone https://github.com/avsDeveloper/OllamaTkinterUi.git
   cd OllamaTkinterUi
   ```

3. **Make executable and run**:
   ```bash
   chmod +x Ollama_Tkinter_Ui.py
   python3 Ollama_Tkinter_Ui.py
   ```

## 🎯 Quick Start

1. **Launch the application**:
   ```bash
   python3 Ollama_Tkinter_Ui.py
   ```

2. **First-time setup**:
   - The app will automatically detect and start the Ollama server
   - If no models are found, use the **Download** button to get popular models
   - Try downloading: `llama3`, `mistral`, `codellama`, or `phi3`

3. **Start chatting**:
   - Select a model from the dropdown
   - Click **"Choose Model"** to load it
   - Type your message after the `>>>` prompt
   - Press **Enter** or click **Send Message**

## 📚 Usage Guide

### Model Management
- **Refresh**: Updates the model list from your Ollama installation
- **Choose Model**: Loads the selected model for chatting
- **Download**: Opens a dialog to download new models from Ollama's library
- **Restart Ollama**: Restarts the Ollama server in user context (useful when models aren't visible)

### Chat Interface
- Type messages after the `>>>` prompt
- Press **Enter** to send messages quickly
- The **Send Message** button provides an alternative to Enter key
- Chat is automatically disabled during model downloads

### System Information
The left panel shows:
- **Selected model** name and status
- **Model size** (e.g., "7B", "13B")
- **RAM usage** when model is loaded
- **GPU/CPU usage** percentages
- **Context window** size (e.g., "4K", "8K")

## 🔧 Troubleshooting

### Common Issues

**"Ollama not found"**
- Make sure Ollama is installed: `ollama --version`
- Check the Help → Installation Guide for setup instructions

**Server won't start**
- Try manually: `ollama serve`
- Check if port 11434 is already in use
- Restart the application

**No models available**
- Download models using the **Download** button
- Or manually: `ollama pull llama3`
- Click **Refresh** to update the model list
- If models still don't appear, try **Restart Ollama** to restart the server in user context

**Chat not responding**
- Ensure a model is selected and loaded (green status indicators)
- Check system logs in the left panel for error messages
- Try reselecting the model

### Performance Tips
- **Smaller models** (like `phi3`) are faster but less capable
- **Larger models** (like `llama3:70b`) are more capable but slower
- **GPU acceleration** significantly improves response times
- **Close other applications** if experiencing memory issues

## 🏗️ Architecture

This GUI is built with:
- **tkinter** - Python's standard GUI toolkit
- **subprocess** - For Ollama CLI integration
- **threading** - Non-blocking operations and background monitoring
- **Pure Python** - No external GUI dependencies required

### File Structure
```
OllamaTkinterUi/
├── Ollama_Tkinter_Ui.py    # Main application
├── README.md               # This documentation
├── LICENSE                 # MIT License
└── deepseek_python_20250801_6294e2.py  # Original development file
```

## 🤝 Contributing

This is designed to be an **extremely simple** interface. Contributions that maintain this simplicity while adding value are welcome:

- **Bug fixes** and stability improvements
- **Better error handling** and user feedback
- **Cross-platform compatibility** (Windows, macOS)
- **UI/UX improvements** that maintain simplicity
- **Documentation** and usage examples

## 📄 License

MIT License - feel free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Ollama team** for the excellent AI model platform
- **Python tkinter** for the simple GUI framework
- **Community** for testing and feedback

---

**Simple. Convenient. Powerful.** 🎯

*For advanced Ollama usage, consider the official Ollama CLI or web-based interfaces. This GUI focuses on simplicity and common use cases.*
