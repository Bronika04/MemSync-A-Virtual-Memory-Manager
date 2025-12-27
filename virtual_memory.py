"""
Virtual Memory Manager
Manages virtual memory allocation and page replacement
"""
import random
import threading
import time
from typing import Dict, List, Tuple, Optional
from utils import ProcessInfo, calculate_pages
from page_replacement import get_algorithm, PageReplacementAlgorithm
import logging


class VirtualMemoryManager:
    """Manages virtual memory for processes"""
    
    def __init__(self, page_size_kb: int, frame_count: int, algorithm_name: str):
        self.page_size_kb = page_size_kb
        self.frame_count = frame_count
        self.algorithm_name = algorithm_name
        self.algorithm = get_algorithm(algorithm_name, frame_count)
        
        self.processes: Dict[int, ProcessInfo] = {}
        self.page_table: Dict[int, Dict[int, Optional[int]]] = {}  # pid -> {page_num -> frame_num}
        self.frame_table: List[Optional[Tuple[int, int]]] = [None] * frame_count  # frame -> (pid, page_num)
        
        self.logger = logging.getLogger("VirtualMemoryManager")
        self.running = False
        self.simulation_thread = None
        self.page_fault_callback = None
        
        self.total_page_faults = 0
        self.total_page_accesses = 0
        self.fault_recovery_times = []
        
        self.lock = threading.Lock()
    
    def add_process(self, process_info: ProcessInfo):
        """Add a process to virtual memory management"""
        with self.lock:
            pid = process_info.pid
            
            # Calculate pages needed
            pages_needed = calculate_pages(process_info.memory_kb, self.page_size_kb)
            process_info.pages_needed = pages_needed
            
            # Initialize page table for process
            self.page_table[pid] = {page_num: None for page_num in range(pages_needed)}
            self.processes[pid] = process_info
            
            # Generate simulated page access sequence
            process_info.page_sequence = self._generate_page_sequence(pages_needed)
            
            self.logger.info(f"Added process {pid} ({process_info.name}) - "
                           f"{process_info.memory_kb}KB, {pages_needed} pages")
    
    def remove_process(self, pid: int):
        """Remove a process from virtual memory management"""
        with self.lock:
            if pid in self.processes:
                # Free frames occupied by this process
                for frame_idx, frame_content in enumerate(self.frame_table):
                    if frame_content and frame_content[0] == pid:
                        self.frame_table[frame_idx] = None
                
                # Remove from tracking
                del self.processes[pid]
                del self.page_table[pid]
                
                self.logger.info(f"Removed process {pid}")
    
    def change_algorithm(self, algorithm_name: str):
        """Change the page replacement algorithm"""
        with self.lock:
            self.algorithm_name = algorithm_name
            self.algorithm = get_algorithm(algorithm_name, self.frame_count)
            self.algorithm.reset()
            
            # Clear all frame allocations
            self.frame_table = [None] * self.frame_count
            for pid in self.page_table:
                for page_num in self.page_table[pid]:
                    self.page_table[pid][page_num] = None
            
            self.logger.info(f"Changed algorithm to {algorithm_name}")
    
    def change_frames(self, new_frame_count: int):
        """Change the number of frames"""
        with self.lock:
            self.frame_count = new_frame_count
            self.algorithm = get_algorithm(self.algorithm_name, new_frame_count)
            
            # Adjust frame table
            if new_frame_count > len(self.frame_table):
                self.frame_table.extend([None] * (new_frame_count - len(self.frame_table)))
            else:
                self.frame_table = self.frame_table[:new_frame_count]
            
            self.logger.info(f"Changed frame count to {new_frame_count}")
    
    def start_simulation(self):
        """Start simulating page accesses"""
        if not self.running:
            self.running = True
            self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self.simulation_thread.start()
            self.logger.info("Memory simulation started")
    
    def stop_simulation(self):
        """Stop simulating page accesses"""
        self.running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=3)
        self.logger.info("Memory simulation stopped")
    
    def _simulation_loop(self):
        """Main simulation loop that simulates page accesses"""
        consecutive_errors = 0
        max_errors = 5
        sleep_time = 0.25  # Even slower simulation for less CPU
        
        while self.running:
            try:
                time.sleep(sleep_time)
                
                # Quick check without lock first
                if not self.processes:
                    consecutive_errors = 0
                    continue
                
                # Minimal lock time
                pid = None
                page_num = None
                page_sequence = None
                
                with self.lock:
                    # Quick operations only inside lock
                    try:
                        pids = list(self.processes.keys())
                        if not pids:
                            continue
                            
                        pid = random.choice(pids)
                        process = self.processes.get(pid)
                        
                        if not process or not process.page_sequence:
                            continue
                        
                        # Get data we need
                        page_num = process.page_sequence[0]
                        page_sequence = process.page_sequence[:50]  # Copy only what we need
                        
                        # Rotate sequence
                        process.page_sequence = process.page_sequence[1:] + [page_num]
                        
                    except (KeyError, IndexError, AttributeError):
                        consecutive_errors += 1
                        if consecutive_errors >= max_errors:
                            self.logger.error("Too many consecutive errors, stopping simulation")
                            self.running = False
                            break
                        continue
                
                # Do the heavy work outside the lock
                if pid and page_num is not None:
                    try:
                        with self.lock:
                            self._access_page(pid, page_num, page_sequence)
                        consecutive_errors = 0
                    except Exception as e:
                        self.logger.error(f"Page access error: {e}")
                        consecutive_errors += 1
                
            except Exception as e:
                self.logger.error(f"Error in simulation loop: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    self.running = False
                    break
                time.sleep(1)
        
        self.logger.info("Simulation loop stopped")
    
    def _access_page(self, pid: int, page_num: int, future_sequence: List[int]):
        """Access a page for a process"""
        # Verify process still exists
        if pid not in self.processes:
            return
            
        self.total_page_accesses += 1
        
        # Check if page is already in a frame
        current_frame = self.page_table[pid].get(page_num)
        
        if current_frame is not None:
            # Page hit
            is_fault, _, recovery_time = self.algorithm.access_page(page_num, future_sequence[:50])  # Limit future sequence
            return
        
        # Page fault - use algorithm to determine replacement
        is_fault, replaced_page, recovery_time = self.algorithm.access_page(
            page_num, future_sequence[:50]  # Limit to prevent memory issues
        )
        
        if is_fault:
            self.total_page_faults += 1
            self.fault_recovery_times.append(recovery_time)
            
            # Limit recovery times list to prevent memory leak
            if len(self.fault_recovery_times) > 10000:
                self.fault_recovery_times = self.fault_recovery_times[-5000:]
            
            # Find or allocate a frame
            frame_idx = self._allocate_frame(pid, page_num, replaced_page)
            
            # Update page table
            self.page_table[pid][page_num] = frame_idx
            
            # Notify callback if registered
            if self.page_fault_callback:
                try:
                    fault_info = {
                        'pid': pid,
                        'process_name': self.processes[pid].name,
                        'page_num': page_num,
                        'frame_num': frame_idx,
                        'replaced_page': replaced_page,
                        'recovery_time_ms': recovery_time,
                        'total_faults': self.total_page_faults,
                        'fault_rate': (self.total_page_faults / self.total_page_accesses * 100)
                    }
                    self.page_fault_callback(fault_info)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
    
    def _allocate_frame(self, pid: int, page_num: int, replaced_page: Optional[int]) -> int:
        """Allocate a frame for a page"""
        # Find empty frame or use replaced frame
        frame_idx = None
        
        # First try to find empty frame
        for idx, content in enumerate(self.frame_table):
            if content is None:
                frame_idx = idx
                break
        
        # If no empty frame, replace according to algorithm
        if frame_idx is None:
            if replaced_page is not None:
                # Find the frame containing the replaced page
                for idx, content in enumerate(self.frame_table):
                    if content and content[1] == replaced_page:
                        frame_idx = idx
                        # Update old process's page table
                        old_pid, old_page = content
                        if old_pid in self.page_table:
                            self.page_table[old_pid][old_page] = None
                        break
            
            # Fallback to first available
            if frame_idx is None:
                frame_idx = 0
        
        # Assign frame
        self.frame_table[frame_idx] = (pid, page_num)
        return frame_idx
    
    def _generate_page_sequence(self, num_pages: int, length: int = 50) -> List[int]:
        """Generate a realistic page access sequence with locality"""
        if num_pages == 0:
            return []
        
        # Reduced from 100 to 50 for better performance
        sequence = []
        current_page = random.randint(0, num_pages - 1)
        
        for _ in range(length):
            sequence.append(current_page)
            
            # 70% chance of locality (nearby page)
            # 30% chance of random jump
            if random.random() < 0.7:
                # Stay in locality
                offset = random.choice([-1, 0, 0, 1])
                current_page = max(0, min(num_pages - 1, current_page + offset))
            else:
                # Random jump
                current_page = random.randint(0, num_pages - 1)
        
        return sequence
    
    def get_statistics(self) -> dict:
        """Get memory management statistics"""
        with self.lock:
            avg_recovery_time = (
                sum(self.fault_recovery_times) / len(self.fault_recovery_times)
                if self.fault_recovery_times else 0
            )
            
            return {
                'total_processes': len(self.processes),
                'total_page_faults': self.total_page_faults,
                'total_page_accesses': self.total_page_accesses,
                'page_fault_rate': (
                    self.total_page_faults / self.total_page_accesses * 100
                    if self.total_page_accesses > 0 else 0
                ),
                'avg_recovery_time_ms': avg_recovery_time,
                'frames_used': sum(1 for f in self.frame_table if f is not None),
                'frames_total': self.frame_count,
                'algorithm_stats': self.algorithm.get_stats()
            }
    
    def get_frame_visualization(self) -> List[dict]:
        """Get frame table for visualization"""
        with self.lock:
            frames = []
            for idx, content in enumerate(self.frame_table):
                if content:
                    pid, page_num = content
                    process = self.processes.get(pid)
                    frames.append({
                        'frame': idx,
                        'pid': pid,
                        'page': page_num,
                        'process_name': process.name if process else 'Unknown'
                    })
                else:
                    frames.append({
                        'frame': idx,
                        'pid': None,
                        'page': None,
                        'process_name': 'Empty'
                    })
            return frames