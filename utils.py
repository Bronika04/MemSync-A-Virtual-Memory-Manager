"""
Utility functions for Virtual Memory Manager
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any


def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}, using defaults")
        return {
            "default_settings": {
                "page_size_kb": 4,
                "frame_count": 10,
                "algorithm": "LRU"
            }
        }


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Setup logging configuration"""
    log_config = config.get("logging", {})
    log_file = log_config.get("file", "logs/vm_manager.log")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get("level", "INFO")),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("VirtualMemoryManager")


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def calculate_pages(memory_size_kb: int, page_size_kb: int) -> int:
    """Calculate number of pages needed"""
    return (memory_size_kb + page_size_kb - 1) // page_size_kb


def get_timestamp() -> str:
    """Get formatted timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class ProcessInfo:
    """Class to store process information"""
    def __init__(self, pid: int, name: str, memory_kb: int):
        self.pid = pid
        self.name = name
        self.memory_kb = memory_kb
        self.pages_needed = 0
        self.loaded_pages = set()
        self.page_sequence = []
        self.creation_time = datetime.now()
        
    def __repr__(self):
        return f"Process({self.pid}, {self.name}, {self.memory_kb}KB)"