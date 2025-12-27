"""
Virtual Memory Manager - Main Entry Point
CSE 5th Semester Project
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import load_config, setup_logging
from process_monitor import ProcessMonitor
from virtual_memory import VirtualMemoryManager
from gui import VirtualMemoryGUI


def main():
    """Main application entry point"""
    print("=" * 60)
    print("Virtual Memory Manager")
    print("BTech CSE - 5th Semester Project")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("Application starting...")
    
    # Get default settings
    settings = config['default_settings']
    
    # Initialize components
    logger.info("Initializing components...")
    
    # Create Virtual Memory Manager
    vm_manager = VirtualMemoryManager(
        page_size_kb=settings['page_size_kb'],
        frame_count=settings['frame_count'],
        algorithm_name=settings['algorithm']
    )
    logger.info(f"Virtual Memory Manager initialized: "
               f"{settings['frame_count']} frames, "
               f"{settings['page_size_kb']}KB page size, "
               f"{settings['algorithm']} algorithm")
    
    # Create Process Monitor
    process_monitor = ProcessMonitor(
        interval=settings.get('monitor_interval_ms', 1000) / 1000.0
    )
    logger.info("Process Monitor initialized")
    
    # Create and run GUI
    logger.info("Starting GUI...")
    gui = VirtualMemoryGUI(config, vm_manager, process_monitor)
    
    print("\nGUI launched successfully!")
    print("\nInstructions:")
    print("1. Click 'Start Monitoring' to begin")
    print("2. Click 'Add Process by PID' or 'Browse All Processes' to add processes")
    print("3. Watch the Frame Table and Page Fault Log for real-time updates")
    print("4. Change algorithms and parameters as needed")
    print("\nNote: The system simulates page accesses for added processes")
    print("=" * 60)
    
    try:
        gui.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("Check logs/vm_manager.log for details")
    finally:
        logger.info("Application shutting down...")
        process_monitor.stop_monitoring()
        vm_manager.stop_simulation()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    main()