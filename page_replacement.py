"""
Page Replacement Algorithms
Implements FIFO, LRU, Optimal, and LFU algorithms
"""
from collections import deque, OrderedDict
from typing import List, Tuple, Optional
import time
import logging


class PageReplacementAlgorithm:
    """Base class for page replacement algorithms"""
    
    def __init__(self, frame_count: int):
        self.frame_count = frame_count
        self.frames = []
        self.page_faults = 0
        self.page_hits = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def access_page(self, page_number: int, future_sequence: List[int] = None) -> Tuple[bool, Optional[int], float]:
        """
        Access a page and handle page fault if necessary
        Returns: (is_page_fault, replaced_page, recovery_time_ms)
        """
        raise NotImplementedError
    
    def reset(self):
        """Reset the algorithm state"""
        self.frames = []
        self.page_faults = 0
        self.page_hits = 0
    
    def get_stats(self) -> dict:
        """Get algorithm statistics"""
        total_accesses = self.page_faults + self.page_hits
        hit_rate = (self.page_hits / total_accesses * 100) if total_accesses > 0 else 0
        return {
            'page_faults': self.page_faults,
            'page_hits': self.page_hits,
            'total_accesses': total_accesses,
            'hit_rate': hit_rate
        }


class FIFO(PageReplacementAlgorithm):
    """First In First Out page replacement"""
    
    def __init__(self, frame_count: int):
        super().__init__(frame_count)
        self.queue = deque()
    
    def access_page(self, page_number: int, future_sequence: List[int] = None) -> Tuple[bool, Optional[int], float]:
        start_time = time.perf_counter()
        
        if page_number in self.frames:
            self.page_hits += 1
            recovery_time = (time.perf_counter() - start_time) * 1000
            return False, None, recovery_time
        
        # Page fault occurred
        self.page_faults += 1
        replaced_page = None
        
        if len(self.frames) < self.frame_count:
            self.frames.append(page_number)
            self.queue.append(page_number)
        else:
            # Replace oldest page (FIFO)
            replaced_page = self.queue.popleft()
            self.frames.remove(replaced_page)
            self.frames.append(page_number)
            self.queue.append(page_number)
        
        recovery_time = (time.perf_counter() - start_time) * 1000
        return True, replaced_page, recovery_time
    
    def reset(self):
        super().reset()
        self.queue = deque()


class LRU(PageReplacementAlgorithm):
    """Least Recently Used page replacement"""
    
    def __init__(self, frame_count: int):
        super().__init__(frame_count)
        self.page_order = OrderedDict()
    
    def access_page(self, page_number: int, future_sequence: List[int] = None) -> Tuple[bool, Optional[int], float]:
        start_time = time.perf_counter()
        
        if page_number in self.frames:
            self.page_hits += 1
            # Move to end (most recently used)
            self.page_order.move_to_end(page_number)
            recovery_time = (time.perf_counter() - start_time) * 1000
            return False, None, recovery_time
        
        # Page fault occurred
        self.page_faults += 1
        replaced_page = None
        
        if len(self.frames) < self.frame_count:
            self.frames.append(page_number)
            self.page_order[page_number] = True
        else:
            # Replace least recently used page
            lru_page = next(iter(self.page_order))
            replaced_page = lru_page
            self.frames.remove(lru_page)
            del self.page_order[lru_page]
            self.frames.append(page_number)
            self.page_order[page_number] = True
        
        recovery_time = (time.perf_counter() - start_time) * 1000
        return True, replaced_page, recovery_time
    
    def reset(self):
        super().reset()
        self.page_order = OrderedDict()


class Optimal(PageReplacementAlgorithm):
    """Optimal page replacement (requires future knowledge)"""
    
    def access_page(self, page_number: int, future_sequence: List[int] = None) -> Tuple[bool, Optional[int], float]:
        start_time = time.perf_counter()
        
        if page_number in self.frames:
            self.page_hits += 1
            recovery_time = (time.perf_counter() - start_time) * 1000
            return False, None, recovery_time
        
        # Page fault occurred
        self.page_faults += 1
        replaced_page = None
        
        if len(self.frames) < self.frame_count:
            self.frames.append(page_number)
        else:
            # Replace page that won't be used for longest time
            if future_sequence:
                farthest_use = -1
                page_to_replace = self.frames[0]
                
                for page in self.frames:
                    try:
                        next_use = future_sequence.index(page)
                    except ValueError:
                        # Page not in future sequence, replace it
                        page_to_replace = page
                        break
                    
                    if next_use > farthest_use:
                        farthest_use = next_use
                        page_to_replace = page
                
                replaced_page = page_to_replace
                self.frames.remove(page_to_replace)
            else:
                # Fallback to FIFO if no future sequence
                replaced_page = self.frames[0]
                self.frames.pop(0)
            
            self.frames.append(page_number)
        
        recovery_time = (time.perf_counter() - start_time) * 1000
        return True, replaced_page, recovery_time


class LFU(PageReplacementAlgorithm):
    """Least Frequently Used page replacement"""
    
    def __init__(self, frame_count: int):
        super().__init__(frame_count)
        self.frequency = {}
        self.time_counter = 0
        self.last_used = {}
    
    def access_page(self, page_number: int, future_sequence: List[int] = None) -> Tuple[bool, Optional[int], float]:
        start_time = time.perf_counter()
        self.time_counter += 1
        
        if page_number in self.frames:
            self.page_hits += 1
            self.frequency[page_number] = self.frequency.get(page_number, 0) + 1
            self.last_used[page_number] = self.time_counter
            recovery_time = (time.perf_counter() - start_time) * 1000
            return False, None, recovery_time
        
        # Page fault occurred
        self.page_faults += 1
        replaced_page = None
        
        if len(self.frames) < self.frame_count:
            self.frames.append(page_number)
        else:
            # Replace least frequently used page (with LRU as tiebreaker)
            min_freq = float('inf')
            lfu_page = None
            oldest_time = float('inf')
            
            for page in self.frames:
                freq = self.frequency.get(page, 0)
                last_time = self.last_used.get(page, 0)
                
                if freq < min_freq or (freq == min_freq and last_time < oldest_time):
                    min_freq = freq
                    lfu_page = page
                    oldest_time = last_time
            
            replaced_page = lfu_page
            self.frames.remove(lfu_page)
            if lfu_page in self.frequency:
                del self.frequency[lfu_page]
            if lfu_page in self.last_used:
                del self.last_used[lfu_page]
            
            self.frames.append(page_number)
        
        self.frequency[page_number] = self.frequency.get(page_number, 0) + 1
        self.last_used[page_number] = self.time_counter
        
        recovery_time = (time.perf_counter() - start_time) * 1000
        return True, replaced_page, recovery_time
    
    def reset(self):
        super().reset()
        self.frequency = {}
        self.time_counter = 0
        self.last_used = {}


def get_algorithm(algorithm_name: str, frame_count: int) -> PageReplacementAlgorithm:
    """Factory function to get page replacement algorithm"""
    algorithms = {
        'FIFO': FIFO,
        'LRU': LRU,
        'Optimal': Optimal,
        'LFU': LFU
    }
    
    if algorithm_name not in algorithms:
        raise ValueError(f"Unknown algorithm: {algorithm_name}")
    
    return algorithms[algorithm_name](frame_count)