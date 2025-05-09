#!/usr/bin/env python
"""
Command-line interface for Auto Face Framing

This module provides the entry point for the 'start-face-framing' command.
"""

import argparse
import sys
import os
import logging
import platform
import time
from typing import Dict, Any, Optional, List, Tuple
import shutil

# Initialize colorama early for Windows terminal color support
import colorama
colorama.init()

from .face_detector import FaceDetector
from .tracker import Tracker
from .camera_stream import CameraStream, load_config
from .utils.video_utils import create_virtual_camera_output, IS_WINDOWS, IS_LINUX, IS_MAC
from .utils.cli_spinner import CLISpinner, SpinnerStyle, RandomSpinner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('autoFaceFraming')

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size (width, height)"""
    return shutil.get_terminal_size((80, 24))

def print_plain_header() -> None:
    """Print a simple ASCII header for terminals that don't support Unicode"""
    print()
    print("=========================================")
    print("          AUTO FACE FRAMING              ")
    print("=========================================")
    print("  Smart camera framing system for all    ")
    print("  your video conferencing needs!         ")
    print("=========================================")
    print()

def print_header(use_fancy_ui: bool = True, use_unicode: bool = True) -> None:
    """Print an attractive header for the application."""
    # If fancy UI is disabled, print a simple header and return
    if not use_fancy_ui:
        print_plain_header()
        return
        
    # If unicode is explicitly disabled, print a simple header and return
    if not use_unicode:
        print_plain_header()
        return
        
    term_width, _ = get_terminal_size()
    
    header = [
        "░█████╗░██╗░░░██╗████████╗░█████╗░  ███████╗░█████╗░░█████╗░███████╗",
        "██╔══██╗██║░░░██║╚══██╔══╝██╔══██╗  ██╔════╝██╔══██╗██╔══██╗██╔════╝",
        "███████║██║░░░██║░░░██║░░░██║░░██║  █████╗░░███████║██║░░╚═╝█████╗░░",
        "██╔══██║██║░░░██║░░░██║░░░██║░░██║  ██╔══╝░░██╔══██║██║░░██╗██╔══╝░░",
        "██║░░██║╚██████╔╝░░░██║░░░╚█████╔╝  ██║░░░░░██║░░██║╚█████╔╝███████╗",
        "╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░░╚════╝░  ╚═╝░░░░░╚═╝░░╚═╝░╚════╝░╚══════╝",
        "",
        "███████╗██████╗░░█████╗░███╗░░░███╗██╗███╗░░██╗░██████╗░",
        "██╔════╝██╔══██╗██╔══██╗████╗░████║██║████╗░██║██╔════╝░",
        "█████╗░░██████╔╝███████║██╔████╔██║██║██╔██╗██║██║░░██╗░",
        "██╔══╝░░██╔══██╗██╔══██║██║╚██╔╝██║██║██║╚████║██║░░╚██╗",
        "██║░░░░░██║░░██║██║░░██║██║░╚═╝░██║██║██║░╚███║╚██████╔╝",
        "╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░╚═╝╚═╝╚═╝░░╚══╝░╚═════╝░"
    ]
    
    # Center the header in the terminal
    padding = max(0, (term_width - len(header[0])) // 2)
    padding_str = " " * padding
    
    print()
    
    # Try to print fancy Unicode header with colors, fall back to plain ASCII if it fails
    try:
        for line in header:
            print(f"{Colors.CYAN}{padding_str}{line}{Colors.RESET}")
        print()
    except UnicodeEncodeError:
        logger.warning("Terminal doesn't support Unicode characters. Falling back to plain ASCII header.")
        print_plain_header()

def print_section_header(text: str) -> None:
    """Print a section header with decorative elements."""
    term_width, _ = get_terminal_size()
    
    # Calculate padding to center the header
    total_length = min(term_width, max(40, len(text) + 10))
    padding = max(0, (term_width - total_length) // 2)
    
    # Calculate inner padding for the text
    inner_padding = max(0, (total_length - len(text) - 4) // 2)
    
    # Prepare the strings
    top_border = padding * " " + "╭" + "─" * (total_length - 2) + "╮"
    bottom_border = padding * " " + "╰" + "─" * (total_length - 2) + "╯"
    text_line = padding * " " + "│" + " " * inner_padding + text + " " * (total_length - len(text) - inner_padding - 2) + "│"
    
    # Print the header
    print()
    print(f"{Colors.YELLOW}{top_border}{Colors.RESET}")
    print(f"{Colors.YELLOW}{text_line}{Colors.RESET}")
    print(f"{Colors.YELLOW}{bottom_border}{Colors.RESET}")
    print()


def print_info_line(label: str, value: str, color_value: str = Colors.RESET) -> None:
    """Print an information line with proper formatting."""
    print(f"{Colors.BRIGHT_WHITE}{label}: {color_value}{value}{Colors.RESET}")


def print_list_item(item: str, indent: int = 2) -> None:
    """Print a list item with bullet point."""
    print(f"{' ' * indent}{Colors.BRIGHT_CYAN}•{Colors.RESET} {item}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the application."""
    parser = argparse.ArgumentParser(
        prog='start-face-framing',  # Consistent program name regardless of how it's invoked
        description='Auto Face Framing Virtual Camera'
    )
    parser.add_argument('--config', type=str, 
                      help='Path to configuration file (default: installed config/settings.yaml)')
    parser.add_argument('--debug', action='store_true', default=None,
                      help='Show debug information on frames (config default: settings.yaml display.show_debug)')
    parser.add_argument('--no-virtual', action='store_true',
                      help='Disable virtual camera output')
    parser.add_argument('--resolution', type=str, default='1280x720',
                      help='Camera resolution (default: 1280x720)')
    parser.add_argument('--fps', type=int, default=24,
                      help='Frame rate (default: 24)')
    parser.add_argument('--no-window', action='store_true',
                      help='Disable preview window even if GUI is available')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    parser.add_argument('--version', action='store_true',
                      help='Show version information and exit')
    parser.add_argument('--camera-index', type=int, default=-1,
                      help='Camera index to use (default: -1 for auto-detection)')
    parser.add_argument('--no-fancy', action='store_true',
                      help='Disable fancy terminal UI')
    parser.add_argument('--no-unicode', action='store_true',
                      help='Disable Unicode characters in terminal output')
    parser.add_argument('--style', type=str, choices=[s.name.lower() for s in SpinnerStyle], default='braille',
                      help='Spinner style for loading animations')
    return parser.parse_args()


def check_dependencies() -> Dict[str, bool]:
    """Check if all required dependencies are installed."""
    with CLISpinner("Checking dependencies", style=SpinnerStyle.BRAILLE) as spinner:
        dependencies = {
            'pyvirtualcam': False,
            'psutil': False,
            'opencv_gui': False
        }
        
        import cv2
        
        # Check for v4l2loopback and pyvirtualcam
        try:
            spinner.update_text("Checking PyVirtualCam")
            import pyvirtualcam
            dependencies['pyvirtualcam'] = True
        except ImportError:
            pass
            
        # Check for psutil (required for system monitoring)
        try:
            spinner.update_text("Checking psutil")
            import psutil
            dependencies['psutil'] = True
        except ImportError:
            pass
        
        # Check if OpenCV has GUI support
        try:
            spinner.update_text("Checking OpenCV GUI support")
            # Try to create a small window to test GUI capability
            cv2.namedWindow("Test", cv2.WINDOW_NORMAL)
            cv2.destroyWindow("Test")
            dependencies['opencv_gui'] = True
        except:
            # If it fails, OpenCV was built without GUI support
            dependencies['opencv_gui'] = False
            
        return dependencies


def ensure_user_config_exists() -> str:
    """
    Ensures user config file exists by copying the default if needed.
    
    Returns:
        Path to the user config file
    """
    # Determine paths
    current_dir = os.getcwd()
    user_config_dir = os.path.join(current_dir, 'config')
    user_config = os.path.join(user_config_dir, 'settings.yaml')
    
    # If user config doesn't exist, create it from default
    if not os.path.exists(user_config):
        # Get default config path
        package_config = os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml')
        
        # Create directory if needed
        if not os.path.exists(user_config_dir):
            os.makedirs(user_config_dir)
            
        # Copy default config to user config
        import shutil
        shutil.copy2(package_config, user_config)
        logger.info(f"Created new user config at {user_config}")
    
    return os.path.abspath(user_config)

def get_default_config_path() -> str:
    """Get the path to the default configuration file."""
    # First try to use the config file in the current directory or project root
    current_dir = os.getcwd()
    user_config = os.path.join(current_dir, 'config', 'settings.yaml')
    
    if os.path.exists(user_config):
        return os.path.abspath(user_config)
    
    # Check one level up in case run from inside a project directory
    parent_config = os.path.join(os.path.dirname(current_dir), 'config', 'settings.yaml')
    if os.path.exists(parent_config):
        return os.path.abspath(parent_config)
    
    # Then try to use the config file in the package directory
    import pkg_resources
    try:
        path = pkg_resources.resource_filename('autoFaceFraming', 'config/settings.yaml')
        if os.path.exists(path):
            return os.path.abspath(path)
    except:
        pass
    
    # Finally fallback to the config file in the package
    package_config = os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml')
    return os.path.abspath(package_config)


def show_version() -> None:
    """Display version information."""
    from . import __version__, __author__, __twitter__, __github__
    
    term_width, _ = get_terminal_size()
    padding = " " * ((term_width - 50) // 2)
    
    print()
    print(f"{padding}{Colors.BOLD}{Colors.BRIGHT_GREEN}Auto Face Framing version {__version__}{Colors.RESET}")
    print(f"{padding}{Colors.BRIGHT_WHITE}Developed by {Colors.BRIGHT_CYAN}{__author__}{Colors.RESET}")
    print(f"{padding}{Colors.BRIGHT_WHITE}Twitter: {Colors.BRIGHT_CYAN}{__twitter__}{Colors.RESET}")
    print(f"{padding}{Colors.BRIGHT_WHITE}GitHub: {Colors.BRIGHT_CYAN}https://github.com/{__github__}{Colors.RESET}")
    print(f"{padding}{Colors.BRIGHT_WHITE}Project: {Colors.BRIGHT_CYAN}https://github.com/{__github__}/autoFaceFraming{Colors.RESET}")
    print()


def show_platform_instructions(fancy: bool = True) -> None:
    """Show platform-specific instructions based on the OS."""
    if IS_WINDOWS:
        if fancy:
            print_section_header("Windows Instructions")
            print_info_line("For Windows", "You need to install a virtual camera driver:", Colors.BRIGHT_YELLOW)
            print_list_item("OBS Virtual Camera (install OBS Studio)")
            print_list_item("Unity Capture (https://github.com/schellingb/UnityCapture)")
            print()
        else:
            print("\nFor Windows, you need to install a virtual camera driver:")
            print("- OBS Virtual Camera (install OBS Studio)")
            print("- Unity Capture (https://github.com/schellingb/UnityCapture)\n")
    
    elif IS_LINUX:
        if fancy:
            print_section_header("Linux Instructions")
            print_info_line("For Linux", "You need v4l2loopback installed:", Colors.BRIGHT_YELLOW)
            print_list_item("Ubuntu/Debian: sudo apt install v4l2loopback-dkms")
            print_list_item("Fedora: sudo dnf install v4l2loopback")
            print_list_item("Load the module with: sudo modprobe v4l2loopback")
            print()
        else:
            print("\nFor Linux, you need v4l2loopback:")
            print("- Ubuntu/Debian: sudo apt install v4l2loopback-dkms")
            print("- Fedora: sudo dnf install v4l2loopback")
            print("- Load the module with: sudo modprobe v4l2loopback\n")
    
    elif IS_MAC:
        if fancy:
            print_section_header("macOS Instructions")
            print_info_line("For macOS", "You need to install a virtual camera driver:", Colors.BRIGHT_YELLOW)
            print_list_item("OBS Virtual Camera (install OBS Studio)")
            print()
        else:
            print("\nFor macOS, you need to install a virtual camera driver:")
            print("- OBS Virtual Camera (install OBS Studio)\n")


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Decide whether to use fancy UI and Unicode
    use_fancy_ui = not args.no_fancy
    use_unicode = not args.no_unicode
    
    # Get spinner style from arguments
    spinner_style = SpinnerStyle[args.style.upper()] if args.style else SpinnerStyle.BRAILLE
    
    # Show version and exit if requested
    if args.version:
        if use_fancy_ui:
            print_header(use_fancy_ui, use_unicode)
        show_version()
        return 0
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Show fancy header
    if use_fancy_ui:
        print_header(use_fancy_ui, use_unicode)
        print_section_header("Starting Auto Face Framing")
    else:
        print("\nStarting Auto Face Framing...\n")
    
    logger.debug("Starting Auto Face Framing")
    
    # Determine configuration file path
    if args.config:
        config_path = args.config
    else:
        # Create user config if it doesn't exist and use that
        config_path = ensure_user_config_exists()
    
    # Load configuration settings
    with CLISpinner("Loading configuration", style=spinner_style) as spinner:
        logger.debug(f"Loading configuration from {config_path}")
        config = load_config(config_path)
        
        # Make it clear which config file is being used in the UI
        config_type = "User config" if "autoFaceFraming/config" not in config_path else "Default config"
        spinner.update_text(f"Loaded {config_type} from {os.path.basename(os.path.dirname(config_path))}/{os.path.basename(config_path)}")
        logger.debug(f"Using {config_type}: {config_path}")
        time.sleep(0.5)  # Small delay for visual effect
    
    # Parse resolution string to width and height
    if 'x' in args.resolution:
        width, height = map(int, args.resolution.split('x'))
    else:
        width, height = 1280, 720
        
    # Default settings in case config is missing
    if not config:
        logger.warning(f"Configuration file not found at {config_path}. Using default settings.")
        camera_resolution = {"width": width, "height": height}
        frame_rate = args.fps
        camera_index = args.camera_index
    else:
        camera_resolution = config.get('camera', {}).get('resolution', {"width": width, "height": height})
        frame_rate = config.get('camera', {}).get('frame_rate', args.fps)
        camera_index = config.get('camera', {}).get('camera_index', args.camera_index)
        
        # Load debug settings from config if command line arg is not provided
        if args.debug is None:  # None means the user didn't explicitly set --debug
            args.debug = config.get('display', {}).get('show_debug', False)

    if use_fancy_ui:
        print_section_header("Configuration")
        print_info_line("Resolution", f"{width}x{height}", Colors.BRIGHT_GREEN)
        print_info_line("Frame rate", f"{frame_rate} fps", Colors.BRIGHT_GREEN)
        print_info_line("Camera index", f"{camera_index}", Colors.BRIGHT_GREEN)
        print_info_line("Debug mode", f"{'Enabled' if args.debug else 'Disabled'}", Colors.BRIGHT_GREEN if args.debug else Colors.BRIGHT_YELLOW) 
        print()
    else:
        print("Initializing Auto Face Framing...")
        print(f"Resolution: {width}x{height}")
        print(f"Frame rate: {frame_rate} fps")
        print(f"Camera index: {camera_index}")
        print(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")
    
    # Check dependencies
    dependencies = check_dependencies()
    
    # Check for virtual camera requirements
    if not args.no_virtual and not dependencies['pyvirtualcam']:
        if use_fancy_ui:
            print_section_header("Missing Dependencies")
            print_info_line("PyVirtualCam", "Not found. Install with: pip install pyvirtualcam", Colors.BRIGHT_RED)
            print()
            show_platform_instructions(fancy=use_fancy_ui)
        else:
            logger.warning("PyVirtualCam not found. Install with: pip install pyvirtualcam")
            show_platform_instructions(fancy=False)
            
        args.no_virtual = True  # Disable virtual camera if module not found

    # Check for psutil (required for system monitoring)
    if not dependencies['psutil']:
        if use_fancy_ui:
            print_info_line("psutil", "Not found. Install with: pip install psutil", Colors.BRIGHT_YELLOW)
            print_info_line("Note", "System monitoring will be disabled in the HUD", Colors.BRIGHT_WHITE)
            print()
        else:
            logger.warning("psutil not found. Install with: pip install psutil")
            logger.warning("System monitoring will be disabled in the HUD")

    # Check if OpenCV has GUI support
    show_window = False
    if not dependencies['opencv_gui']:
        if use_fancy_ui:
            print_info_line("OpenCV GUI Support", "Not available", Colors.BRIGHT_YELLOW)
            if IS_WINDOWS:
                print_info_line("Note", "To enable GUI on Windows, ensure you have the OpenCV with GUI support installed.", Colors.BRIGHT_WHITE)
            elif IS_LINUX:
                print_info_line("Note", "To enable GUI on Linux, install the GTK+ development libraries and rebuild OpenCV.", Colors.BRIGHT_WHITE)
            elif IS_MAC:
                print_info_line("Note", "To enable GUI on macOS, ensure you have a properly built version of OpenCV.", Colors.BRIGHT_WHITE)
            print()
        else:
            logger.info("Notice: OpenCV was built without GUI support. Preview window will be disabled.")
            if IS_WINDOWS:
                logger.info("To enable GUI on Windows, ensure you have the OpenCV with GUI support installed.")
            elif IS_LINUX:
                logger.info("To enable GUI on Linux, install the GTK+ development libraries and rebuild OpenCV.")
            elif IS_MAC:
                logger.info("To enable GUI on macOS, ensure you have a properly built version of OpenCV.")
        show_window = False
    elif args.no_window:
        if use_fancy_ui:
            print_info_line("Preview Window", "Disabled by user request", Colors.BRIGHT_YELLOW)
            print()
        else:
            logger.info("Preview window disabled by user request.")
        show_window = False
    else:
        if use_fancy_ui:
            print_info_line("Preview Window", "Enabled", Colors.BRIGHT_GREEN)
            print()
        else:
            logger.info("Preview window will be shown.")
        show_window = True

    if use_fancy_ui:
        print_section_header("Starting Camera")
        print_info_line("Debug HUD overlay", "Enabled" if args.debug else "Disabled", Colors.BRIGHT_GREEN if args.debug else Colors.BRIGHT_YELLOW)
        print_info_line("Output", "Virtual camera" if not args.no_virtual else "Display only", Colors.BRIGHT_GREEN if not args.no_virtual else Colors.BRIGHT_YELLOW)
        print_info_line("Preview window", "Enabled" if show_window else "Disabled", Colors.BRIGHT_GREEN if show_window else Colors.BRIGHT_YELLOW)
        print_info_line("Operating system", f"{platform.system()} {platform.release()}", Colors.BRIGHT_CYAN)
        print()
        print_info_line("Controls", "Press Ctrl+C in the terminal to stop the application", Colors.BRIGHT_MAGENTA)
        print()
    else:
        print("\nStarting camera with the following settings:")
        print(f"- Debug HUD overlay: {'Enabled' if args.debug else 'Disabled'}")
        print(f"- Output: {'Display only' if args.no_virtual else 'Virtual camera'}")
        print(f"- Preview window: {'Disabled' if not show_window else 'Enabled'}")
        print(f"- Operating system: {platform.system()} {platform.release()}")
        print("\nPress Ctrl+C in the terminal to stop the application")

    # Start camera stream
    camera_stream = None
    try:
        with CLISpinner("Initializing camera", style=spinner_style) as spinner:
            camera_stream = CameraStream(
                width=camera_resolution,
                height=height,
                fps=frame_rate,
                camera_index=camera_index
            )
            spinner.update_text("Camera initialized successfully")
            time.sleep(0.5)  # Small delay for visual effect
        
        with CLISpinner("Starting video processing", style=spinner_style) as spinner:
            spinner.update_text("Starting face detection")
            time.sleep(0.5)  # Small delay for visual effect
            spinner.update_text("Configuring tracking")
            time.sleep(0.5)  # Small delay for visual effect
            spinner.update_text("Preparing output streams")
            time.sleep(0.5)  # Small delay for visual effect
        
        if use_fancy_ui:
            print_section_header("Camera Started")
            print_info_line("Status", "Running", Colors.BRIGHT_GREEN)
            print()
        
        # Start the main processing loop
        camera_stream.start_stream(
            show_debug=args.debug,  # This now respects the config file setting
            virtual_output=not args.no_virtual,
            show_window=show_window
        )
        
        return 0
        
    except KeyboardInterrupt:
        if use_fancy_ui:
            print()
            print_section_header("Application Stopped")
            print_info_line("Reason", "User interrupted (Ctrl+C)", Colors.BRIGHT_YELLOW)
            print()
        else:
            logger.info("\nApplication stopped by user")
        return 0
    except Exception as e:
        if use_fancy_ui:
            print()
            print_section_header("Error")
            print_info_line("Error Type", f"{type(e).__name__}", Colors.BRIGHT_RED)
            print_info_line("Message", f"{str(e)}", Colors.BRIGHT_RED)
            print()
            print("Traceback:")
            import traceback
            traceback.print_exc()
            print()
        else:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
        return 1
    finally:
        # Make sure to release resources
        if camera_stream is not None:
            with CLISpinner("Closing camera and releasing resources", style=spinner_style) as spinner:
                camera_stream.release()
                spinner.update_text("Resources released successfully")
                time.sleep(0.5)  # Small delay for visual effect
        
        if use_fancy_ui:
            print_section_header("Application Terminated")
            print_info_line("Status", "All resources released", Colors.BRIGHT_GREEN)
            print()
        else:
            logger.info("Application terminated.")


if __name__ == "__main__":
    sys.exit(main())