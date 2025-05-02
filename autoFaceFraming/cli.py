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
from typing import Dict, Any, Optional

from .face_detector import FaceDetector
from .tracker import Tracker
from .camera_stream import CameraStream, load_config
from .utils.video_utils import create_virtual_camera_output, IS_WINDOWS, IS_LINUX, IS_MAC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('autoFaceFraming')

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the application."""
    parser = argparse.ArgumentParser(description='Auto Face Framing Virtual Camera')
    parser.add_argument('--config', type=str, 
                      help='Path to configuration file (default: installed config/settings.yaml)')
    parser.add_argument('--debug', action='store_true', default=True,
                      help='Show debug information on frames (default: True)')
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
    return parser.parse_args()


def check_dependencies() -> Dict[str, bool]:
    """Check if all required dependencies are installed."""
    dependencies = {
        'pyvirtualcam': False,
        'psutil': False,
        'opencv_gui': False
    }
    
    import cv2
    
    # Check for v4l2loopback and pyvirtualcam
    try:
        import pyvirtualcam
        dependencies['pyvirtualcam'] = True
    except ImportError:
        pass
        
    # Check for psutil (required for system monitoring)
    try:
        import psutil
        dependencies['psutil'] = True
    except ImportError:
        pass
    
    # Check if OpenCV has GUI support
    try:
        # Try to create a small window to test GUI capability
        cv2.namedWindow("Test", cv2.WINDOW_NORMAL)
        cv2.destroyWindow("Test")
        dependencies['opencv_gui'] = True
    except:
        # If it fails, OpenCV was built without GUI support
        dependencies['opencv_gui'] = False
        
    return dependencies


def get_default_config_path() -> str:
    """Get the path to the default configuration file."""
    # First try to use the config file in the current directory
    if os.path.exists('config/settings.yaml'):
        return 'config/settings.yaml'
    
    # Then try to use the config file in the package directory
    import pkg_resources
    try:
        path = pkg_resources.resource_filename('autoFaceFraming', 'config/settings.yaml')
        if os.path.exists(path):
            return path
    except:
        pass
    
    # Finally fallback to the config file in the package
    return os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml')


def show_version() -> None:
    """Display version information."""
    from . import __version__, __author__, __twitter__, __github__
    print(f"Auto Face Framing version {__version__}")
    print(f"Developed by {__author__}")
    print(f"Twitter: {__twitter__}")
    print(f"GitHub: https://github.com/{__github__}")
    print(f"Project: https://github.com/{__github__}/autoFaceFraming")
    

def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Show version and exit if requested
    if args.version:
        show_version()
        return 0
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.debug("Starting Auto Face Framing")
    
    # Determine configuration file path
    if args.config:
        config_path = args.config
    else:
        config_path = get_default_config_path()
    
    # Load configuration settings
    logger.debug(f"Loading configuration from {config_path}")
    config = load_config(config_path)
    
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

    print("Initializing Auto Face Framing...")
    print(f"Resolution: {width}x{height}")
    print(f"Frame rate: {frame_rate} fps")
    print(f"Camera index: {camera_index}")
    
    # Check dependencies
    dependencies = check_dependencies()
    
    # Check for virtual camera requirements
    if not args.no_virtual and not dependencies['pyvirtualcam']:
        logger.warning("PyVirtualCam not found. Install with: pip install pyvirtualcam")
        
        # OS-specific instructions
        if IS_WINDOWS:
            logger.warning("For Windows, you also need to install one of these virtual camera drivers:")
            logger.warning("- OBS Virtual Camera (install OBS Studio)")
            logger.warning("- Unity Capture (https://github.com/schellingb/UnityCapture)")
        elif IS_LINUX:
            logger.warning("For Linux, you also need v4l2loopback:")
            logger.warning("- Ubuntu/Debian: sudo apt install v4l2loopback-dkms")
            logger.warning("- Fedora: sudo dnf install v4l2loopback")
            logger.warning("Load the module with: sudo modprobe v4l2loopback")
        elif IS_MAC:
            logger.warning("For macOS, you also need to install a virtual camera driver:")
            logger.warning("- OBS Virtual Camera (install OBS Studio)")
            
        args.no_virtual = True  # Disable virtual camera if module not found

    # Check for psutil (required for system monitoring)
    if not dependencies['psutil']:
        logger.warning("psutil not found. Install with: pip install psutil")
        logger.warning("System monitoring will be disabled in the HUD")

    # Check if OpenCV has GUI support
    show_window = False
    if not dependencies['opencv_gui']:
        logger.info("Notice: OpenCV was built without GUI support. Preview window will be disabled.")
        if IS_WINDOWS:
            logger.info("To enable GUI on Windows, ensure you have the OpenCV with GUI support installed.")
        elif IS_LINUX:
            logger.info("To enable GUI on Linux, install the GTK+ development libraries and rebuild OpenCV.")
        elif IS_MAC:
            logger.info("To enable GUI on macOS, ensure you have a properly built version of OpenCV.")
        show_window = False
    elif args.no_window:
        logger.info("Preview window disabled by user request.")
        show_window = False
    else:
        logger.info("Preview window will be shown.")
        show_window = True

    print("\nStarting camera with the following settings:")
    print(f"- Debug HUD overlay: {'Enabled' if args.debug else 'Disabled'}")
    print(f"- Output: {'Display only' if args.no_virtual else 'Virtual camera'}")
    print(f"- Preview window: {'Disabled' if not show_window else 'Enabled'}")
    print(f"- Operating system: {platform.system()} {platform.release()}")
    print("\nPress Ctrl+C in the terminal to stop the application")

    # Start camera stream
    camera_stream = None
    try:
        camera_stream = CameraStream(
            width=camera_resolution,
            height=height,
            fps=frame_rate,
            camera_index=camera_index
        )
        
        # Start the main processing loop
        camera_stream.start_stream(
            show_debug=args.debug, 
            virtual_output=not args.no_virtual,
            show_window=show_window
        )
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nApplication stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Make sure to release resources
        if camera_stream is not None:
            camera_stream.release()
        
        logger.info("Application terminated.")


if __name__ == "__main__":
    sys.exit(main()) 