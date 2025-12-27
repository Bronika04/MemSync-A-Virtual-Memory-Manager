"""
Enhanced GUI for Virtual Memory Manager
Modern design with proper scrolling and visibility
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from typing import Dict
from utils import format_size


class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(self, bg='#f5f6fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        self.scrollable_frame.bind('<Enter>', lambda e: self._bind_mousewheel(canvas))
        self.scrollable_frame.bind('<Leave>', lambda e: self._unbind_mousewheel(canvas))
        
    def _bind_mousewheel(self, canvas):
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
    def _unbind_mousewheel(self, canvas):
        canvas.unbind_all("<MouseWheel>")


class VirtualMemoryGUI:
    """Enhanced GUI Application for Virtual Memory Manager"""
    
    def __init__(self, config: Dict, vm_manager, process_monitor):
        self.config = config
        self.vm_manager = vm_manager
        self.process_monitor = process_monitor
        
        self.root = tk.Tk()
        self.root.title("Virtual Memory Manager - Enhanced Edition")
        self.root.geometry("1600x900")
        self.root.state('zoomed')  # Start maximized
        
        # Modern color scheme
        self.colors = {
            'bg': '#f5f6fa',
            'primary': '#3498db',
            'success': '#2ecc71',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'white': '#ffffff',
            'text_dark': '#2c3e50',
            'text_light': '#7f8c8d'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        self.running = False
        self.update_thread = None
        self.update_scheduled = False  # Prevent multiple scheduled updates
        self.last_update_time = 0  # Track last update time
        
        # Style configuration
        self._setup_styles()
        self._create_widgets()
        self._setup_callbacks()
        
        # Set up periodic update using after() instead of thread
        self.update_interval = 1500  # 1.5 seconds between updates
        
    def _setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Treeview
        style.configure("Treeview",
                       background=self.colors['white'],
                       foreground=self.colors['text_dark'],
                       rowheight=28,
                       fieldbackground=self.colors['white'],
                       borderwidth=0)
        style.map('Treeview', background=[('selected', self.colors['primary'])])
        
        style.configure("Treeview.Heading",
                       background=self.colors['dark'],
                       foreground=self.colors['white'],
                       relief="flat",
                       font=('Segoe UI', 10, 'bold'))
        style.map("Treeview.Heading",
                 background=[('active', self.colors['primary'])])
        
    def _create_widgets(self):
        """Create all GUI widgets with proper scrolling"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid for main container
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # === HEADER ===
        self._create_header(main_container)
        
        # === SCROLLABLE CONTENT AREA ===
        # Create canvas for scrolling
        canvas = tk.Canvas(main_container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky="nsew", padx=15, pady=(10, 15))
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(10, 15))
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Make canvas expand with window
        def _configure_canvas(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        
        canvas.bind('<Configure>', _configure_canvas)
        
        # === CONTENT LAYOUT ===
        content_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights for responsive layout
        content_frame.columnconfigure(0, weight=0, minsize=350)  # Left panel fixed width
        content_frame.columnconfigure(1, weight=1)  # Right panel expandable
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel container
        left_panel = tk.Frame(content_frame, bg=self.colors['bg'])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Right panel container
        right_panel = tk.Frame(content_frame, bg=self.colors['bg'])
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Configure right panel grid
        right_panel.rowconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        right_panel.rowconfigure(2, weight=1)
        right_panel.columnconfigure(0, weight=1)
        
        # === LEFT PANEL WIDGETS ===
        self._create_control_panel(left_panel)
        self._create_statistics_panel(left_panel)
        
        # === RIGHT PANEL WIDGETS ===
        self._create_process_panel(right_panel)
        self._create_frame_table_panel(right_panel)
        self._create_log_panel(right_panel)
        
    def _create_header(self, parent):
        """Create modern header with title and status"""
        header = tk.Frame(parent, bg=self.colors['primary'], height=70)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        
        # Title
        title_label = tk.Label(
            header,
            text="🖥️ Virtual Memory Manager",
            font=('Segoe UI', 22, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Status indicator
        self.status_frame = tk.Frame(header, bg=self.colors['primary'])
        self.status_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.status_indicator = tk.Canvas(
            self.status_frame,
            width=16,
            height=16,
            bg=self.colors['primary'],
            highlightthickness=0
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        self.status_circle = self.status_indicator.create_oval(2, 2, 14, 14, fill=self.colors['danger'], outline="")
        
        self.status_label = tk.Label(
            self.status_frame,
            text="System Stopped",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        self.status_label.pack(side=tk.LEFT)
        
    def _create_control_panel(self, parent):
        """Create control panel with modern design"""
        control_card = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        control_card.pack(fill=tk.X, pady=(0, 15))
        
        header = tk.Label(
            control_card,
            text="⚙️ Configuration",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['dark'],
            anchor='w'
        )
        header.pack(fill=tk.X, padx=15, pady=(15, 12))
        
        content = tk.Frame(control_card, bg=self.colors['white'])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Algorithm Selection
        self._create_labeled_widget(
            content,
            "Page Replacement Algorithm:",
            self._create_algorithm_selector(content),
            row=0
        )
        
        # Page Size
        self._create_labeled_widget(
            content,
            "Page Size (KB):",
            self._create_page_size_selector(content),
            row=1
        )
        
        # Frame Count
        frame_control_frame = tk.Frame(content, bg=self.colors['white'])
        self._create_labeled_widget(
            content,
            "Number of Frames:",
            frame_control_frame,
            row=2
        )
        
        self.frame_count_var = tk.IntVar(value=self.config['default_settings']['frame_count'])
        frame_spinbox = ttk.Spinbox(
            frame_control_frame,
            from_=self.config['frame_ranges']['min'],
            to=self.config['frame_ranges']['max'],
            textvariable=self.frame_count_var,
            width=8,
            font=('Segoe UI', 10),
            increment=5
        )
        frame_spinbox.pack(side=tk.LEFT, padx=(0, 8))
        
        apply_btn = tk.Button(
            frame_control_frame,
            text="Apply",
            command=self._on_frame_change,
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor='hand2'
        )
        apply_btn.pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(content, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Control Buttons
        btn_frame = tk.Frame(content, bg=self.colors['white'])
        btn_frame.pack(fill=tk.X)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start Monitoring",
            command=self._start_system,
            bg=self.colors['success'],
            fg=self.colors['white'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.start_btn.pack(fill=tk.X, pady=(0, 8))
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏸ Stop Monitoring",
            command=self._stop_system,
            bg=self.colors['danger'],
            fg=self.colors['white'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor='hand2',
            state='disabled'
        )
        self.stop_btn.pack(fill=tk.X, pady=(0, 8))
        
        reset_btn = tk.Button(
            btn_frame,
            text="🔄 Reset Statistics",
            command=self._reset_stats,
            bg=self.colors['warning'],
            fg=self.colors['white'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        reset_btn.pack(fill=tk.X)
        
    def _create_labeled_widget(self, parent, label_text, widget, row):
        """Helper to create labeled widgets"""
        container = tk.Frame(parent, bg=self.colors['white'])
        container.pack(fill=tk.X, pady=6)
        
        label = tk.Label(
            container,
            text=label_text,
            font=('Segoe UI', 9),
            bg=self.colors['white'],
            fg=self.colors['text_dark'],
            anchor='w'
        )
        label.pack(fill=tk.X, pady=(0, 4))
        
        widget.pack(fill=tk.X)
        
    def _create_algorithm_selector(self, parent):
        """Create algorithm selector"""
        self.algorithm_var = tk.StringVar(value=self.config['default_settings']['algorithm'])
        combo = ttk.Combobox(
            parent,
            textvariable=self.algorithm_var,
            values=self.config['algorithms'],
            state='readonly',
            font=('Segoe UI', 10)
        )
        combo.bind('<<ComboboxSelected>>', self._on_algorithm_change)
        return combo
        
    def _create_page_size_selector(self, parent):
        """Create page size selector"""
        self.page_size_var = tk.IntVar(value=self.config['default_settings']['page_size_kb'])
        combo = ttk.Combobox(
            parent,
            textvariable=self.page_size_var,
            values=self.config['page_sizes'],
            state='readonly',
            font=('Segoe UI', 10)
        )
        return combo
        
    def _create_statistics_panel(self, parent):
        """Create statistics panel with fixed height"""
        stats_card = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT)
        stats_card.pack(fill=tk.BOTH, expand=True)
        
        header = tk.Label(
            stats_card,
            text="📊 Statistics",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['dark'],
            anchor='w'
        )
        header.pack(fill=tk.X, padx=15, pady=(15, 12))
        
        # Stats display with scrollbar
        stats_container = tk.Frame(stats_card, bg=self.colors['white'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Create text widget with scrollbar
        stats_scroll = ttk.Scrollbar(stats_container)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stats_text = tk.Text(
            stats_container,
            font=('Consolas', 9),
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            relief=tk.FLAT,
            padx=12,
            pady=12,
            wrap=tk.WORD,
            height=20,
            yscrollcommand=stats_scroll.set
        )
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scroll.config(command=self.stats_text.yview)
        
        # Store current scroll position
        self.stats_scroll_position = 0.0
        
    def _create_process_panel(self, parent):
        """Create enhanced process management panel"""
        process_card = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT)
        process_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        header_frame = tk.Frame(process_card, bg=self.colors['white'])
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        header = tk.Label(
            header_frame,
            text="📋 Process Management",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['dark'],
            anchor='w'
        )
        header.pack(side=tk.LEFT)
        
        # Process count badge
        self.process_count_label = tk.Label(
            header_frame,
            text="0 processes",
            font=('Segoe UI', 8, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white'],
            padx=10,
            pady=3
        )
        self.process_count_label.pack(side=tk.RIGHT)
        
        # Button toolbar
        btn_toolbar = tk.Frame(process_card, bg=self.colors['white'])
        btn_toolbar.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        add_pid_btn = tk.Button(
            btn_toolbar,
            text="➕ Add by PID",
            command=self._add_process_dialog,
            bg=self.colors['success'],
            fg=self.colors['white'],
            font=('Segoe UI', 8, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        add_pid_btn.pack(side=tk.LEFT, padx=(0, 6))
        
        browse_btn = tk.Button(
            btn_toolbar,
            text="🔍 Browse",
            command=self._browse_processes,
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=('Segoe UI', 8, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        browse_btn.pack(side=tk.LEFT, padx=(0, 6))
        
        self.remove_btn = tk.Button(
            btn_toolbar,
            text="🗑️ Remove",
            command=self._remove_selected_process,
            bg=self.colors['danger'],
            fg=self.colors['white'],
            font=('Segoe UI', 8, 'bold'),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        self.remove_btn.pack(side=tk.LEFT)
        
        # Process Treeview with scrollbar
        tree_container = tk.Frame(process_card, bg=self.colors['white'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        tree_scroll = ttk.Scrollbar(tree_container)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.process_tree = ttk.Treeview(
            tree_container,
            columns=('PID', 'Name', 'Memory', 'Pages', 'Status'),
            show='headings',
            height=8,
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.process_tree.yview)
        
        self.process_tree.heading('PID', text='PID')
        self.process_tree.heading('Name', text='Process Name')
        self.process_tree.heading('Memory', text='Memory')
        self.process_tree.heading('Pages', text='Pages')
        self.process_tree.heading('Status', text='Status')
        
        self.process_tree.column('PID', width=60, anchor='center')
        self.process_tree.column('Name', width=180)
        self.process_tree.column('Memory', width=100, anchor='center')
        self.process_tree.column('Pages', width=60, anchor='center')
        self.process_tree.column('Status', width=80, anchor='center')
        
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add alternating row colors
        self.process_tree.tag_configure('oddrow', background='#f9f9f9')
        self.process_tree.tag_configure('evenrow', background='#ffffff')
        
    def _create_frame_table_panel(self, parent):
        """Create frame table panel"""
        frame_card = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT)
        frame_card.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        header_frame = tk.Frame(frame_card, bg=self.colors['white'])
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        header = tk.Label(
            header_frame,
            text="🗂️ Frame Table",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['dark'],
            anchor='w'
        )
        header.pack(side=tk.LEFT)
        
        # Frame usage badge
        self.frame_usage_label = tk.Label(
            header_frame,
            text="0/0 frames",
            font=('Segoe UI', 8, 'bold'),
            bg=self.colors['warning'],
            fg=self.colors['white'],
            padx=10,
            pady=3
        )
        self.frame_usage_label.pack(side=tk.RIGHT)
        
        tree_container = tk.Frame(frame_card, bg=self.colors['white'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        frame_scroll = ttk.Scrollbar(tree_container)
        frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.frame_tree = ttk.Treeview(
            tree_container,
            columns=('Frame', 'PID', 'Page', 'Process'),
            show='headings',
            height=8,
            yscrollcommand=frame_scroll.set
        )
        frame_scroll.config(command=self.frame_tree.yview)
        
        self.frame_tree.heading('Frame', text='Frame #')
        self.frame_tree.heading('PID', text='PID')
        self.frame_tree.heading('Page', text='Page #')
        self.frame_tree.heading('Process', text='Process')
        
        self.frame_tree.column('Frame', width=80, anchor='center')
        self.frame_tree.column('PID', width=80, anchor='center')
        self.frame_tree.column('Page', width=80, anchor='center')
        self.frame_tree.column('Process', width=200)
        
        self.frame_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Color coding for frames
        self.frame_tree.tag_configure('empty', background='#ecf0f1', foreground='#95a5a6')
        self.frame_tree.tag_configure('occupied', background='#d5f4e6', foreground='#27ae60')
        
    def _create_log_panel(self, parent):
        """Create page fault log panel"""
        log_card = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT)
        log_card.grid(row=2, column=0, sticky="nsew")
        
        header = tk.Label(
            log_card,
            text="📝 Page Fault Log",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['dark'],
            anchor='w'
        )
        header.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        log_container = tk.Frame(log_card, bg=self.colors['white'])
        log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 8),
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored log entries
        self.log_text.tag_configure('fault', foreground=self.colors['danger'], font=('Consolas', 8, 'bold'))
        self.log_text.tag_configure('info', foreground=self.colors['primary'])
        self.log_text.tag_configure('success', foreground=self.colors['success'])
        
    def _setup_callbacks(self):
        """Setup callbacks for VM manager"""
        self.vm_manager.page_fault_callback = self._on_page_fault
    
    def _start_system(self):
        """Start monitoring and simulation"""
        if self.running:
            return  # Prevent multiple starts
            
        self.running = True
        self.process_monitor.start_monitoring()
        self.vm_manager.start_simulation()
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Update status indicator
        self.status_indicator.itemconfig(self.status_circle, fill=self.colors['success'])
        self.status_label.config(text="System Running")
        
        # Start periodic updates using root.after (no separate thread needed)
        self._schedule_update()
        
        self._log("✅ System started successfully", 'success')
    
    def _stop_system(self):
        """Stop monitoring and simulation"""
        self.running = False
        self.process_monitor.stop_monitoring()
        self.vm_manager.stop_simulation()
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        # Update status indicator
        self.status_indicator.itemconfig(self.status_circle, fill=self.colors['danger'])
        self.status_label.config(text="System Stopped")
        
        self._log("⏸️ System stopped", 'info')
    
    def _schedule_update(self):
        """Schedule the next update using root.after()"""
        if not self.running or not self.root or not self.root.winfo_exists():
            return
        
        # Perform update
        self._safe_update_displays()
        
        # Schedule next update
        if self.running:
            self.root.after(self.update_interval, self._schedule_update)
    
    def _update_loop(self):
        """Update GUI periodically"""
        while self.running:
            try:
                # Schedule update on main thread
                if self.root and self.root.winfo_exists():
                    try:
                        self.root.after(0, self._safe_update_displays)
                    except tk.TclError:
                        break
                else:
                    break
                    
                time.sleep(1.0)  # Increased from 0.5s to reduce load
            except Exception as e:
                print(f"Update loop error: {e}")
                break
        
        print("Update loop stopped")
    
    def _safe_update_displays(self):
        """Safely update all display elements with error handling"""
        try:
            if not self.root or not self.root.winfo_exists():
                return
            if not self.running:
                return
            
            # Throttle updates - prevent too frequent updates
            current_time = time.time()
            if current_time - self.last_update_time < 1.0:  # Minimum 1 second between updates
                return
            
            self.last_update_time = current_time
            
            # Update displays efficiently
            self._update_process_list()
            self._update_frame_table()
            self._update_statistics()
            
        except tk.TclError as e:
            print(f"TclError in display update: {e}")
            self.running = False
        except Exception as e:
            print(f"Display update error: {e}")
    
    def _update_displays(self):
        """Update all display elements"""
        self._safe_update_displays()
    
    def _update_process_list(self):
        """Update the process list"""
        try:
            # Get current items to avoid unnecessary updates
            current_items = set(self.process_tree.get_children())
            processes = self.process_monitor.get_tracked_processes()
            
            # Check if update is needed
            if len(current_items) == len(processes):
                # Quick check - if count matches, might not need full update
                return
            
            # Clear and rebuild
            for item in current_items:
                self.process_tree.delete(item)
            
            # Add tracked processes
            for idx, process in enumerate(processes):
                status = "✓ Active" if self.running else "⏸ Paused"
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                
                self.process_tree.insert('', tk.END, values=(
                    process.pid,
                    process.name,
                    format_size(process.memory_kb * 1024),
                    process.pages_needed,
                    status
                ), tags=(tag,))
            
            # Update process count badge
            self.process_count_label.config(text=f"{len(processes)} process{'es' if len(processes) != 1 else ''}")
        except Exception as e:
            print(f"Process list update error: {e}")
    
    def _update_frame_table(self):
        """Update the frame table display"""
        try:
            # Clear existing items
            for item in self.frame_tree.get_children():
                self.frame_tree.delete(item)
            
            # Add frame information
            frames = self.vm_manager.get_frame_visualization()
            occupied_count = 0
            
            for frame_info in frames:
                if frame_info['pid'] is not None:
                    tag = 'occupied'
                    occupied_count += 1
                    self.frame_tree.insert('', tk.END, values=(
                        f"Frame {frame_info['frame']}",
                        frame_info['pid'],
                        frame_info['page'],
                        frame_info['process_name']
                    ), tags=(tag,))
                else:
                    tag = 'empty'
                    self.frame_tree.insert('', tk.END, values=(
                        f"Frame {frame_info['frame']}",
                        "—",
                        "—",
                        "Empty"
                    ), tags=(tag,))
            
            # Update frame usage badge
            total_frames = len(frames)
            self.frame_usage_label.config(text=f"{occupied_count}/{total_frames} frames")
            
            # Color code based on usage percentage
            usage_pct = (occupied_count / total_frames * 100) if total_frames > 0 else 0
            if usage_pct < 50:
                self.frame_usage_label.config(bg=self.colors['success'])
            elif usage_pct < 80:
                self.frame_usage_label.config(bg=self.colors['warning'])
            else:
                self.frame_usage_label.config(bg=self.colors['danger'])
        except Exception as e:
            print(f"Frame table update error: {e}")
    
    def _update_statistics(self):
        """Update statistics display without auto-scrolling"""
        try:
            stats = self.vm_manager.get_statistics()
            
            # CRITICAL: Save scroll position BEFORE any changes
            try:
                scroll_position = self.stats_text.yview()
                saved_position = scroll_position[0] if scroll_position else 0.0
            except:
                saved_position = 0.0
            
            # Disable auto-scroll by preventing text widget from updating view
            self.stats_text.config(state='normal')
            
            stats_text = f"""
╔══════════════════════════════════╗
║      SYSTEM STATISTICS           ║
╚══════════════════════════════════╝

📊 Process Information
   • Active Processes: {stats['total_processes']}
   • Total Frames: {stats['frames_total']}
   • Frames in Use: {stats['frames_used']}
   • Frame Usage: {(stats['frames_used']/stats['frames_total']*100) if stats['frames_total'] > 0 else 0:.1f}%

📄 Page Management
   • Total Accesses: {stats['total_page_accesses']:,}
   • Page Faults: {stats['total_page_faults']:,}
   • Fault Rate: {stats['page_fault_rate']:.2f}%
   • Hit Rate: {100 - stats['page_fault_rate']:.2f}%

⚡ Performance Metrics
   • Avg Recovery: {stats['avg_recovery_time_ms']:.3f} ms
   • Best Recovery: {min(self.vm_manager.fault_recovery_times) if self.vm_manager.fault_recovery_times else 0:.3f} ms
   • Worst Recovery: {max(self.vm_manager.fault_recovery_times) if self.vm_manager.fault_recovery_times else 0:.3f} ms

⚙️ Current Configuration
   • Algorithm: {self.vm_manager.algorithm_name}
   • Page Size: {self.vm_manager.page_size_kb} KB
   • Total Memory: {stats['frames_total'] * self.vm_manager.page_size_kb} KB
   • Used Memory: {stats['frames_used'] * self.vm_manager.page_size_kb} KB

📈 Algorithm Performance
   • Page Hits: {stats['algorithm_stats']['page_hits']}
   • Hit Rate: {stats['algorithm_stats']['hit_rate']:.2f}%
            """.strip()
            
            # Update text content
            self.stats_text.delete('1.0', tk.END)
            self.stats_text.insert('1.0', stats_text)
            
            # CRITICAL: Restore exact scroll position to prevent auto-scrolling
            self.stats_text.yview_moveto(saved_position)
            
        except Exception as e:
            print(f"Statistics update error: {e}")
    
    def _on_algorithm_change(self, event=None):
        """Handle algorithm change"""
        new_algorithm = self.algorithm_var.get()
        self.vm_manager.change_algorithm(new_algorithm)
        self._log(f"🔄 Algorithm changed to {new_algorithm}", 'info')
    
    def _on_frame_change(self, event=None):
        """Handle frame count change"""
        new_frame_count = self.frame_count_var.get()
        self.vm_manager.change_frames(new_frame_count)
        self._log(f"🔄 Frame count changed to {new_frame_count}", 'info')
    
    def _add_process_dialog(self):
        """Show modern dialog to add process by PID"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Process by PID")
        dialog.geometry("400x200")
        dialog.configure(bg=self.colors['white'])
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Content
        content = tk.Frame(dialog, bg=self.colors['white'])
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        title = tk.Label(
            content,
            text="Enter Process ID",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['dark']
        )
        title.pack(pady=(0, 20))
        
        pid_label = tk.Label(
            content,
            text="PID:",
            font=('Segoe UI', 10),
            bg=self.colors['white'],
            fg=self.colors['text_dark']
        )
        pid_label.pack(anchor='w', pady=(0, 5))
        
        pid_entry = tk.Entry(
            content,
            font=('Segoe UI', 12),
            relief=tk.FLAT,
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            insertbackground=self.colors['primary']
        )
        pid_entry.pack(fill=tk.X, ipady=8)
        pid_entry.focus()
        
        def add_process():
            try:
                pid = int(pid_entry.get())
                process_info = self.process_monitor.add_process_to_track(pid)
                if process_info:
                    self.vm_manager.add_process(process_info)
                    self._log(f"✅ Added process: {process_info.name} (PID: {pid})", 'success')
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Could not add process.\n\nPossible reasons:\n• Invalid PID\n• Access denied\n• Process not found")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numeric PID")
        
        btn_frame = tk.Frame(content, bg=self.colors['white'])
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        add_btn = tk.Button(
            btn_frame,
            text="Add Process",
            command=add_process,
            bg=self.colors['success'],
            fg=self.colors['white'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        add_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        
        # Bind Enter key
        pid_entry.bind('<Return>', lambda e: add_process())
    
    def _browse_processes(self):
        """Show modern dialog to browse all processes"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Browse Processes")
        dialog.geometry("800x600")
        dialog.configure(bg=self.colors['white'])
        
        # Center dialog
        dialog.transient(self.root)
        
        # Header
        header = tk.Frame(dialog, bg=self.colors['primary'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="🔍 Browse Running Processes",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['primary'],
            fg=self.colors['white']
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Search frame
        search_frame = tk.Frame(dialog, bg=self.colors['white'])
        search_frame.pack(fill=tk.X, padx=20, pady=20)
        
        search_label = tk.Label(
            search_frame,
            text="🔎 Search:",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['text_dark']
        )
        search_label.pack(side=tk.LEFT, padx=(0, 10))
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=search_var,
            font=('Segoe UI', 11),
            relief=tk.FLAT,
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            insertbackground=self.colors['primary']
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        search_entry.focus()
        
        # Clear button
        clear_btn = tk.Button(
            search_frame,
            text="✕",
            command=lambda: search_var.set(""),
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=8,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Info label for results count
        info_frame = tk.Frame(dialog, bg=self.colors['white'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        results_label = tk.Label(
            info_frame,
            text="Loading processes...",
            font=('Segoe UI', 9),
            bg=self.colors['white'],
            fg=self.colors['text_light'],
            anchor='w'
        )
        results_label.pack(side=tk.LEFT)
        
        # Process list
        tree_frame = tk.Frame(dialog, bg=self.colors['white'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('PID', 'Name', 'Memory'),
            show='headings',
            height=15
        )
        tree.heading('PID', text='Process ID')
        tree.heading('Name', text='Process Name')
        tree.heading('Memory', text='Memory Usage')
        
        tree.column('PID', width=100, anchor='center')
        tree.column('Name', width=350)
        tree.column('Memory', width=150, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add alternating colors
        tree.tag_configure('oddrow', background='#f9f9f9')
        tree.tag_configure('evenrow', background='#ffffff')
        
        def refresh_list(search_term=""):
            for item in tree.get_children():
                tree.delete(item)
            
            processes = self.process_monitor.get_all_processes()
            # Sort by name
            processes.sort(key=lambda x: x['name'].lower())
            
            # Filter processes based on search term
            filtered_processes = []
            search_lower = search_term.lower()
            
            for proc in processes:
                # Search in process name and PID
                if (search_lower in proc['name'].lower() or 
                    search_term in str(proc['pid']) or
                    search_term == ""):
                    filtered_processes.append(proc)
            
            # Update results count
            total_count = len(processes)
            filtered_count = len(filtered_processes)
            
            if search_term:
                results_label.config(
                    text=f"Found {filtered_count} of {total_count} processes matching '{search_term}'",
                    fg=self.colors['primary']
                )
            else:
                results_label.config(
                    text=f"Showing all {total_count} processes",
                    fg=self.colors['text_light']
                )
            
            # Populate tree with filtered results
            for idx, proc in enumerate(filtered_processes):
                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                tree.insert('', tk.END, values=(
                    proc['pid'],
                    proc['name'],
                    format_size(proc['memory_kb'] * 1024)
                ), tags=(tag,))
            
            # Show message if no results
            if filtered_count == 0 and search_term:
                results_label.config(
                    text=f"No processes found matching '{search_term}'",
                    fg=self.colors['danger']
                )
        
        def on_search(*args):
            refresh_list(search_var.get())
        
        # Real-time search as user types
        search_var.trace('w', on_search)
        
        # Search on Enter key
        search_entry.bind('<Return>', lambda e: refresh_list(search_var.get()))
        
        # Popular process shortcuts
        shortcut_frame = tk.Frame(dialog, bg=self.colors['white'])
        shortcut_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        shortcuts_label = tk.Label(
            shortcut_frame,
            text="Quick Search:",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['white'],
            fg=self.colors['text_dark']
        )
        shortcuts_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Common process shortcuts
        shortcuts = [
            ("Chrome", "chrome"),
            ("Notepad", "notepad"),
            ("Explorer", "explorer"),
            ("VS Code", "code"),
            ("Python", "python")
        ]
        
        for label, keyword in shortcuts:
            btn = tk.Button(
                shortcut_frame,
                text=label,
                command=lambda k=keyword: search_var.set(k),
                bg=self.colors['light'],
                fg=self.colors['text_dark'],
                font=('Segoe UI', 8),
                relief=tk.FLAT,
                padx=8,
                pady=3,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['primary'], fg=self.colors['white']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.colors['light'], fg=self.colors['text_dark']))
        
        def add_selected():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                pid = int(item['values'][0])
                name = item['values'][1]
                
                process_info = self.process_monitor.add_process_to_track(pid)
                if process_info:
                    self.vm_manager.add_process(process_info)
                    self._log(f"✅ Added process: {name} (PID: {pid})", 'success')
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", f"Could not add process {name} (PID: {pid})\n\nTry running as Administrator")
            else:
                messagebox.showwarning("No Selection", "Please select a process first")
        
        # Double-click to add
        tree.bind('<Double-1>', lambda e: add_selected())
        
        # Button frame
        btn_frame = tk.Frame(dialog, bg=self.colors['white'])
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        add_btn = tk.Button(
            btn_frame,
            text="➕ Add Selected Process",
            command=add_selected,
            bg=self.colors['success'],
            fg=self.colors['white'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=lambda: refresh_list(search_var.get()),
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bg=self.colors['light'],
            fg=self.colors['text_dark'],
            font=('Segoe UI', 11, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        refresh_list()
    
    def _remove_selected_process(self):
        """Remove selected process from tracking (works during simulation)"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a process to remove")
            return
        
        item = self.process_tree.item(selection[0])
        pid = int(item['values'][0])
        name = item['values'][1]
        
        # Confirm removal
        result = messagebox.askyesno(
            "Confirm Removal",
            f"Remove process from monitoring?\n\nProcess: {name}\nPID: {pid}\n\nThis will free all frames used by this process.",
            icon='warning'
        )
        
        if result:
            # Remove from both monitor and VM manager
            self.process_monitor.remove_process_from_tracking(pid)
            self.vm_manager.remove_process(pid)
            self._log(f"🗑️ Removed process: {name} (PID: {pid})", 'info')
            
            # Update display immediately
            self._update_displays()
    
    def _reset_stats(self):
        """Reset all statistics"""
        result = messagebox.askyesno(
            "Reset Statistics",
            "Are you sure you want to reset all statistics?\n\nThis will clear:\n• Page fault counts\n• Page access counts\n• Recovery time data",
            icon='question'
        )
        
        if result:
            self.vm_manager.total_page_faults = 0
            self.vm_manager.total_page_accesses = 0
            self.vm_manager.fault_recovery_times = []
            self.vm_manager.algorithm.reset()
            self._log("🔄 Statistics reset", 'info')
    
    def _on_page_fault(self, fault_info: dict):
        """Handle page fault notification"""
        log_msg = (f"⚠️  PAGE FAULT | Process: {fault_info['process_name']} (PID: {fault_info['pid']}) | "
                  f"Page {fault_info['page_num']} → Frame {fault_info['frame_num']} | "
                  f"Recovery: {fault_info['recovery_time_ms']:.3f} ms | "
                  f"Total: {fault_info['total_faults']}")
        
        # Use root.after to schedule log update instead of calling directly
        if self.root and self.root.winfo_exists():
            self.root.after(0, lambda: self._log(log_msg, 'fault'))
    
    def _log(self, message: str, tag='info'):
        """Add message to log with color coding"""
        try:
            if not self.root or not self.root.winfo_exists():
                return
                
            timestamp = self._get_timestamp()
            full_message = f"[{timestamp}] {message}\n"
            
            self.log_text.insert(tk.END, full_message, tag)
            self.log_text.see(tk.END)
            
            # Keep log size manageable - limit to 500 lines
            lines = int(self.log_text.index('end-1c').split('.')[0])
            if lines > 500:
                self.log_text.delete('1.0', '250.0')  # Delete first half
        except tk.TclError:
            pass  # Widget destroyed
        except Exception as e:
            print(f"Logging error: {e}")
    
    def _get_timestamp(self):
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def run(self):
        """Run the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Add welcome message
        self._log("🚀 Virtual Memory Manager initialized", 'success')
        self._log("📌 Click 'Start Monitoring' to begin", 'info')
        
        self.root.mainloop()
    
    def _on_closing(self):
        """Handle window closing"""
        print("Window closing...")
        
        if self.running:
            result = messagebox.askyesno(
                "Confirm Exit",
                "System is currently running.\n\nDo you want to stop and exit?",
                icon='warning'
            )
            if not result:
                return
        
        # Stop all threads
        self.running = False
        
        try:
            if self.process_monitor:
                self.process_monitor.stop_monitoring()
            if self.vm_manager:
                self.vm_manager.stop_simulation()
        except Exception as e:
            print(f"Error stopping services: {e}")
        
        # Wait for threads to finish
        time.sleep(0.5)
        
        # Destroy window
        try:
            self.root.destroy()
        except:
            pass
        
        print("Application closed")