"""
Process Monitor for Windows
Monitors real processes and their memory usage
"""
import psutil
import threading
import time
from typing import List, Dict, Callable
from utils import ProcessInfo
import logging


class ProcessMonitor:
    """Monitor Windows processes and their memory usage"""
    
    def __init__(self, callback: Callable = None, interval: float = 1.0):
        self.callback = callback
        self.interval = interval
        self.running = False
        self.monitor_thread = None
        self.tracked_processes: Dict[int, ProcessInfo] = {}
        self.logger = logging.getLogger("ProcessMonitor")
        self.process_filter = set()  # PIDs to specifically track
        
    def start_monitoring(self):
        """Start monitoring processes"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Process monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring processes"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("Process monitoring stopped")
    
    def add_process_to_track(self, pid: int):
        """Add a specific process to track"""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            memory_kb = memory_info.rss // 1024
            
            proc_info = ProcessInfo(
                pid=pid,
                name=process.name(),
                memory_kb=memory_kb
            )
            
            self.process_filter.add(pid)
            self.tracked_processes[pid] = proc_info
            
            if self.callback:
                self.callback('new_process', proc_info)
            
            self.logger.info(f"Now tracking process: {proc_info}")
            return proc_info
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.error(f"Cannot track process {pid}: {e}")
            return None
    
    def remove_process_from_tracking(self, pid: int):
        """Remove a process from tracking"""
        if pid in self.process_filter:
            self.process_filter.remove(pid)
        if pid in self.tracked_processes:
            del self.tracked_processes[pid]
            if self.callback:
                self.callback('process_removed', pid)
    
    def get_all_processes(self) -> List[Dict]:
        """Get list of all running processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'memory_kb': info['memory_info'].rss // 1024
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
    
    def get_tracked_processes(self) -> List[ProcessInfo]:
        """Get list of currently tracked processes"""
        return list(self.tracked_processes.values())
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        consecutive_errors = 0
        max_errors = 10
        
        while self.running:
            try:
                time.sleep(self.interval)  # Sleep first to reduce initial load
                
                # Check if tracked processes are still running
                pids_to_check = list(self.tracked_processes.keys())
                
                for pid in pids_to_check:
                    try:
                        if not psutil.pid_exists(pid):
                            self.logger.info(f"Process {pid} terminated")
                            self.remove_process_from_tracking(pid)
                        else:
                            # Update memory usage (less frequently)
                            process = psutil.Process(pid)
                            memory_kb = process.memory_info().rss // 1024
                            
                            if pid in self.tracked_processes:
                                old_memory = self.tracked_processes[pid].memory_kb
                                self.tracked_processes[pid].memory_kb = memory_kb
                                
                                # Notify if significant memory change (5MB threshold)
                                if abs(memory_kb - old_memory) > 5120:
                                    if self.callback:
                                        try:
                                            self.callback('memory_change', self.tracked_processes[pid])
                                        except Exception as e:
                                            self.logger.error(f"Callback error: {e}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        pass
                    except Exception as e:
                        self.logger.error(f"Error checking process {pid}: {e}")
                
                consecutive_errors = 0  # Reset on successful iteration
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    self.logger.error("Too many consecutive errors, stopping monitor")
                    self.running = False
                    break
                time.sleep(2)  # Wait longer before retrying
        
        self.logger.info("Process monitoring stopped")
    
    def get_process_by_name(self, name: str) -> List[Dict]:
        """Find processes by name"""
        matching = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if name.lower() in proc.info['name'].lower():
                    matching.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_kb': proc.info['memory_info'].rss // 1024
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return matching
    
    def get_file_processes(self, filepath: str) -> List[Dict]:
        """Get processes associated with a file"""
        # This is a simplified version - in reality, would need to check open files
        filename = filepath.split('\\')[-1].split('.')[0]
        return self.get_process_by_name(filename)