# PyQuick Project

## Project Introduction
PyQuick is a Python-based toolset project designed to provide practical functions for rapid development and deployment. The project includes build scripts, utility modules, and dependency management configuration.

## Project Structure
### Core Files
- [python_tool.py](file:///Users/li/Documents/GitHub/pyquick/python_tool.py): Core functionality implementation file, providing Python version downloads, pip management (upgrade, install, uninstall packages), and theme switching
- [build.bat](file:///Users/li/Documents/GitHub/pyquick/build.bat): Windows platform build script for packaging Python scripts into standalone Windows executables
- [requirements.txt](file:///Users/li/Documents/GitHub/pyquick/requirements.txt): Project dependency list containing all Python libraries required for operation

### Other Important Files
- LICENSE.txt: Full text of GNU General Public License
- README.md: Project documentation containing introduction, installation guide, and usage instructions

## Key Features
1. Supports cross-platform building
2. Provides common utility functions
3. Complete dependency management configuration

## Python_Tool Features

### Main Functional Modules

#### 1. Python Version Download
Supports downloading specified Python installers from python.org

#### 2. pip Management
- **pip Upgrade**: Automatically upgrades to the latest version
- **Package Management**: Supports installing/uninstalling Python packages

#### 3. Theme Switching
Supports dark/light mode switching with automatic preference saving

## Installation Guide
```bash
# Install dependencies
pip install -r requirements.txt
# or use pip3 if macOS
pip3 install -r requirements.txt
```

## Usage Instructions
1. Run [python_tool.py](file:///Users/li/Documents/GitHub/pyquick/python_tool.py) to launch the application
2. In "Python Download" tab select Python version and download path, click "Download" to start
3. In "pip Management" tab you can upgrade pip or install/uninstall Python packages
4. In main window menu you can switch themes, view about information, and export logs

## Technology Stack
- Python 3.x
- Tkinter: Used to build the graphical user interface
- Nuitka: Tool for compiling Python scripts into executables
- Requests: HTTP request library for file downloads
- Wget: Network dataset download tool
- sv_ttk: Sun Valley theme package providing modern interface style
- BeautifulSoup4 and lxml: HTML parsing libraries