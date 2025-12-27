# MemSync – A Virtual Memory Management System

![MemSync Logo](Logo.png)

## Intoduction
MemSync is a Virtual Memory Management system designed to simulate and visualize memory allocation, page replacement algorithms, and process behavior in an operating system environment. The project provides a GUI-based interface to monitor memory usage and observe how different page replacement strategies work in real time.
[Live Demo]

## Features
- Simulates virtual memory management
- Implements page replacement algorithms
- Real-time process monitoring
- Interactive GUI-based visualization
- Configurable page size and frame count
- Logs memory operations and page faults

## Concepts Used
- Operating System (Virtual Memory)
- Paging & Page Replacement Algorithms
- Memory Management

## Tech Stack
- Backend: Python
- GUI: Tkinter
- Core Concepts: OS Memory Management
- Version Control: Git & GitHub

## Project Structure
```
src/
│── gui.py                     # GUI interface for interaction
│── main.py                    # Main entry point of the application
│── page_replacement.py        # Page replacement algorithms
│── process_monitor.py         # Process monitoring logic
│── utils.py                   # Helper utilities and configuration
│── virtual_memory.py          # Core virtual memory logic
│── web_app.py                 # Web-based interface launcher
│
├── logs/                       # Application logs
├── __pycache__/                # Compiled Python files
│
└── README.md                   # Project documentation
```

## Installation
### 1. Clone the Repository
```sh
git clone https://github.com/Bronika04/MemSync-A-Virtual-Memory-Manager.git
cd MemSync-A-Virtual-Memory-Manager
```

### 2. Create Virtual Environment
```sh
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Run the Application
```sh
python web_app.py
```
The application will start locally and launch the GUI.

## How It Works
1. Start the application: [MemSync Live]
2. Choose memory parameters such as page size and number of frames.
3. Add processes manually or through process monitoring.
4. Observe page faults, memory allocation, and algorithm behavior.

## Contact
For any queries, reach out at [bronika2005@gmail.com](mailto:supriyasuman2005@gmail.com)
