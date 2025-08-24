# Ollama Tkinter GUI

A **feature-rich and intuitive** Python-based graphical user interface for [Ollama](https://ollama.ai), providing comprehensive AI chat functionality with advanced features like token tracking, response control, and intelligent model management.

<img width="1404" height="964" alt="Screenshot from 2025-08-04 13-01-24" src="https://github.com/user-attachments/assets/b0c847c6-1ebf-4700-bcb1-2c304244bf8a" />

## 🚀 Overview

This is a comprehensive yet user-friendly GUI wrapper for Ollama that makes it easy to:
- **Automatically manage** the Ollama server (starts/stops as needed)
- **Browse and select** installed models with detailed information
- **Download new models** with progress tracking and cancellation
- **Chat interactively** with real-time token usage monitoring
- **Control response generation** with stop functionality and timeout configuration
- **Filter model reasoning** with <think> tag toggle
- **Monitor system resources** and model performance
- **View detailed logs** of all operations with intelligent filtering

Perfect for users who want a powerful desktop interface with advanced AI chat features while maintaining ease of use.

## ✨ Features

### 🤖 **Advanced Model Management**
- **Auto-discovery** of installed Ollama models with real-time updates
- **One-click model selection** with comprehensive information display
- **Model downloading** with real-time progress tracking and cancellation support
- **Detailed model information** showing size, RAM usage, GPU/CPU utilization, and context window
- **Smart model preloading** for faster response times

### 💬 **Intelligent Chat Interface**
- **Real-time chat** with selected AI models and streaming responses
- **Token usage tracking** with color-coded warnings (🟢 green, 🟠 orange, 🔴 red)
- **Dynamic token counter** showing current usage vs. model context limit
- **Response control** with stop generation button for immediate cancellation
- **<think> tag filtering** - toggle to show/hide model reasoning processes
- **Configurable timeouts** for model response handling
- **Enter key support** for quick message sending
- **Professional chat formatting** with proper message structure

### 🎛️ **Response Control & Monitoring**
- **Stop Generation** - instantly cancel ongoing model responses
- **Token Counter** - real-time display with warnings (⚡ at 80%, ⚠️ at 90% usage)
- **Response Timeout** - configurable timeout settings (default 60s)
- **Thinking Toggle** - show/hide model <think> reasoning tags
- **Conversation History** - automatic tracking for accurate token counting
- **Context Management** - smart handling of conversation context limits

### 🔧 **Smart Server Management**
- **Automatic server startup** - no manual `ollama serve` needed
- **Intelligent server detection** - knows if server was started by system or user
- **Server restart functionality** - easily restart server in user context  
- **Background server monitoring** with real-time status updates
- **Graceful shutdown** handling with process cleanup
- **Multi-path detection** for various Ollama installations

### 📊 **Advanced System Monitoring**
- **Server status indicator** - shows if started by system or user with color coding
- **Real-time system logs** with intelligent filtering (reduced repetitive messages)
- **Model resource usage** (RAM, GPU/CPU percentages) with live updates
- **Download progress tracking** with status indicators and cancellation
- **Loading states** for all operations with visual feedback
- **Token usage analytics** with conversation history tracking

### 🎨 **Professional User Experience**
- **Optimized layout** - Send/Stop buttons with token counter in bottom-right
- **Server status section** with restart button for easy server management
- **Professional UI** with 1400x900 window size and responsive design
- **Modal dialogs** for downloads and installation guides
- **Keyboard shortcuts** (Enter to send, Escape to cancel dialogs)
- **Built-in installation guide** accessible from Help menu
- **Smart button states** - context-aware enabling/disabling
- **Visual indicators** - warning icons for high token usage

## 🛠️ Requirements

- **Python 3.6+** with tkinter (usually included)
- **Ollama** installed on your system
- **Linux/Unix environment** (tested on Linux, should work on macOS/Windows)

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
   - Check server status above the model dropdown
   - If no models are found, use the **Download** button to get popular models
   - Try downloading: `llama3`, `mistral`, `codellama`, or `phi3`

3. **Start chatting**:
   - Select a model from the dropdown
   - Wait for model info to load (shows resource usage and context window)
   - Notice the token counter in bottom-right showing "Tokens: 0 / [limit]"
   - Type your message in the input field
   - Press **Enter** or click **Send** to chat
   - Watch token usage update in real-time
   - Use **Stop** button to cancel responses if needed

## 🎮 Usage

### **Starting the Application**
```bash
python3 Ollama_Tkinter_Ui.py
```

### **Server Management**
- **Automatic Startup**: Server starts automatically when app opens
- **Server Status**: Check status in the server section above model dropdown
  - 🟢 "Started by user" (green) - server started in user context, all models visible
  - � "Started by system" (orange) - system-managed server, may have limited access  
  - 🔴 "Not running" (red) - server offline
- **Restart Server**: Click "Restart Ollama" to restart in user context if needed

### **Advanced Chat Features**
1. **Token Management**:
   - Monitor token usage in bottom-right corner
   - Green (< 60%) = Safe usage
   - Orange (60-80%) = Caution ⚡
   - Red (> 80%) = Critical ⚠️
   - Automatic conversation history tracking

2. **Response Control**:
   - **Stop Generation**: Click "Stop" to cancel ongoing responses
   - **Response Timeout**: Configure timeout (default 60s) in left panel
   - **Think Tag Toggle**: Show/hide model reasoning with checkbox

3. **Conversation Management**:
   - Automatic token counting for entire conversation
   - Context window tracking per model
   - Conversation resets when changing models

### **Chatting with Models**
1. **Select a model** from the dropdown (automatically populates with available models)
2. **Wait for model info** to load (shows RAM usage, GPU/CPU utilization, context size)
3. **Configure options** as needed:
   - Set response timeout (default 60 seconds)
   - Toggle "Show model reasoning" for <think> tags
4. **Type your message** in the input field
5. **Press Enter** or click "Send" to chat
6. **Monitor token usage** in bottom-right corner
7. **Use Stop button** to cancel responses if needed

### **Downloading Models**
1. Click **"Download"** button next to model dropdown
2. **Enter model name** (e.g., `llama3.2`, `qwen2.5:7b`)
3. **Watch progress** with real-time download tracking
4. **Cancel anytime** if needed

### **System Logs**
- **Monitor operations** in the left panel log area
- **Intelligent filtering** - reduced repetitive server monitoring messages
- **Track downloads**, model loading, server status, and all system operations
- **Debug information** available for troubleshooting

### **Installation Guide**
- Access via **Help > Installation Guide** menu
- **Step-by-step** Ollama installation instructions
- **Platform-specific** guidance for Linux, macOS, and Windows
- **Copy functionality** for easy command copying

## 📚 Usage Guide

### Model Management
- **Refresh**: Updates the model list from your Ollama installation
- **Choose Model**: Loads the selected model and resets conversation history
- **Download**: Opens a dialog to download new models from Ollama's library
- **Restart Ollama**: Restarts the Ollama server in user context (useful when models aren't visible)

### Chat Interface
- **Message Input**: Type messages in the input field at the bottom
- **Send Options**: Press **Enter** or click **Send Message** button
- **Stop Generation**: Click **Stop** button to cancel ongoing responses
- **Token Tracking**: Monitor usage in bottom-right corner with color warnings
- **Response Control**: Configure timeout and thinking tag visibility
- **Auto-formatting**: Chat messages appear with proper formatting and structure

### Advanced Features
- **Token Counter**: Real-time display of conversation length vs. model limits
  - Format: "Tokens: current / max" (e.g., "Tokens: 1,234 / 8K")
  - Color coding: Green → Orange → Red with warning icons
- **<think> Tag Control**: Toggle to show/hide model reasoning processes
- **Response Timeout**: Configurable timeout for model responses (default 60s)
- **Conversation History**: Automatic tracking for accurate token counting
- **Context Management**: Smart handling when approaching model limits

### System Information & Monitoring
The left panel shows:
- **Server status** - whether started by user or system (with color coding)
- **Selected model** name and loading status
- **Model details** - size, RAM usage, GPU/CPU utilization, context window
- **Response timeout** configuration with set button
- **Think tag toggle** - checkbox to control reasoning visibility
- **Real-time logs** - filtered system events and operations
- **Debug information** - process detection and server management details

### Server Status Indicator
Located above the model dropdown:
- 🟢 **"Started by user"** (green) - optimal state, all models accessible
- � **"Started by system"** (orange) - system-managed, may have limited model access
- 🔴 **"Not running"** (red) - server offline, needs startup
- **Restart button** - click to restart server in user context
- **Real-time updates** - status changes automatically detected

## 🔧 Troubleshooting

### Common Issues

**"Ollama not found"**
- Make sure Ollama is installed: `ollama --version`
- Check the Help → Installation Guide for setup instructions

**Server won't start**
- Try manually: `ollama serve`
- Check if port 11434 is already in use
- Use the **Restart Ollama** button to restart in user context
- Check server status indicator above model dropdown

**Server context issues (models not visible)**
- � "Started by system" - server running but limited model access
- Click **Restart Ollama** to restart server in user context
- After restart, status should show 🟢 "Started by user"
- This is the most common fix for model visibility issues

**No models available**
- Download models using the **Download** button
- Or manually: `ollama pull llama3`
- Click **Refresh** to update the model list
- If models still don't appear, try **Restart Ollama** to restart the server in user context

**Chat not responding**
- Ensure a model is selected and loaded (check model info display)
- Check system logs in the left panel for error messages
- Try reselecting the model
- Verify server status is 🟢 "Started by user"
- Use **Stop** button if response seems stuck

**Token counter showing red/warning**
- ⚡ **Orange (80% usage)**: Approaching context limit, consider starting new conversation
- ⚠️ **Red (90%+ usage)**: Critical - very close to context limit
- **Solution**: Choose new model to reset conversation history
- **Tip**: Monitor token usage to manage long conversations

**Model responses cut off or incomplete**
- Check if you hit the **Stop** button accidentally
- Verify response timeout setting (increase if needed)
- Look for timeout messages in system logs
- Try increasing timeout in left panel configuration

**<think> tags appearing in responses**
- These are model reasoning processes
- Toggle **"Show model reasoning (<think> tags)"** checkbox to hide them
- Unchecked = cleaner responses, Checked = see model thinking process

### Performance Tips
- **Monitor token usage** to avoid hitting context limits
- **Smaller models** (like `phi3`) are faster but less capable
- **Larger models** (like `llama3:70b`) are more capable but slower
- **GPU acceleration** significantly improves response times
- **Close other applications** if experiencing memory issues
- **User context servers** generally provide better model access than system servers
- **Use Stop button** to cancel unwanted responses quickly
- **Adjust timeout** based on your system performance and model size

## 🏗️ Architecture

This GUI is built with:
- **tkinter** - Python's standard GUI toolkit for cross-platform compatibility
- **subprocess** - For Ollama CLI integration and process management
- **threading** - Non-blocking operations and background monitoring
- **requests** - HTTP communication with Ollama API for streaming responses
- **re** - Regular expressions for text filtering and parsing
- **Pure Python** - No external GUI dependencies required

### Key Components
- **OllamaGUI Class** - Main application with comprehensive feature set
- **Token Management** - Real-time conversation tracking and context monitoring
- **Server Management** - Intelligent Ollama server detection and control
- **Response Control** - Stop generation and timeout management
- **Model Information** - Detailed model stats and resource monitoring
- **Chat Interface** - Professional messaging with filtering capabilities

### File Structure
```
OllamaTkinterUi/
├── Ollama_Tkinter_Ui.py    # Main application (1,600+ lines)
├── README.md               # Comprehensive documentation
├── LICENSE                 # MIT License
└── screenshots/            # Application screenshots
```

## 🚀 New Features in Latest Version

### 🎯 **Token Counter & Management**
- **Real-time token tracking** with conversation history
- **Color-coded warnings** (Green → Orange → Red)
- **Visual indicators** (⚡ at 80%, ⚠️ at 90% usage)
- **Context window detection** from model information
- **Automatic conversation reset** when changing models

### 🛑 **Response Control**
- **Stop Generation** button for immediate response cancellation
- **Configurable timeouts** with easy adjustment
- **Smart button states** - context-aware enabling/disabling
- **HTTP request cancellation** for clean stop functionality

### 🧠 **<think> Tag Filtering**
- **Toggle model reasoning** visibility with checkbox
- **Smart filtering** during streaming responses
- **Cleaner conversation** display when disabled
- **Preserved context** for token counting regardless of filter state

### 🎨 **Enhanced UI/UX**
- **Optimized button layout** with token counter placement
- **Intelligent log filtering** - reduced repetitive messages
- **Professional status indicators** with improved color coding
- **Better error handling** and user feedback

## 🤝 Contributing

This project balances **powerful features** with **ease of use**. Contributions that enhance this balance are welcome:

- **Feature improvements** that maintain simplicity
- **Bug fixes** and stability enhancements
- **Cross-platform compatibility** (Windows, macOS testing)
- **Performance optimizations** for better responsiveness
- **UI/UX improvements** with accessibility in mind
- **Documentation** and usage examples
- **Token management** enhancements
- **Response control** improvements

### Development Guidelines
- Maintain the **single-file architecture** for easy distribution
- Keep **dependencies minimal** (prefer standard library)
- **Test thoroughly** with various models and scenarios
- **Document new features** comprehensively
- **Preserve backwards compatibility** when possible

## 📄 License

MIT License - feel free to use, modify, and distribute.

## 🙏 Acknowledgments

- **Ollama team** for the excellent AI model platform
- **Python tkinter** for the simple GUI framework
- **Community** for testing and feedback

---

**Powerful. Intuitive. Feature-Rich.** 🎯

*A comprehensive GUI that brings advanced AI chat capabilities to your desktop while maintaining ease of use. Perfect for both casual users and power users who need sophisticated conversation management.*
