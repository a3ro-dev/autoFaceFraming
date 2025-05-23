import cv2
import numpy as np
import time
import platform
import os
import sys
from typing import List, Tuple, Optional, Dict, Any, Union, Callable
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Check for pyvirtualcam
try:
    import pyvirtualcam
    VIRTUAL_CAM_AVAILABLE = True
except ImportError:
    VIRTUAL_CAM_AVAILABLE = False
    logger.warning("PyVirtualCam not available. Install with: pip install pyvirtualcam")

# Check operating system
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MAC = platform.system() == "Darwin"

def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    Resize a frame to specified dimensions.
    
    Args:
        frame: Input frame
        width: Target width
        height: Target height
        
    Returns:
        Resized frame
    """
    return cv2.resize(frame, (width, height))

def apply_filter(frame: np.ndarray, filter_type: str) -> np.ndarray:
    """
    Apply a visual filter to a frame.
    
    Args:
        frame: Input frame
        filter_type: Type of filter to apply ('blur', 'gray', etc.)
        
    Returns:
        Filtered frame
    """
    if filter_type == 'blur':
        return cv2.GaussianBlur(frame, (15, 15), 0)
    elif filter_type == 'gray':
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif filter_type == 'edge':
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, 100, 200)
    return frame

def stabilize_frame(prev_frame: np.ndarray, 
                   curr_frame: np.ndarray, 
                   prev_transform: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Stabilizes video using feature matching and motion estimation.
    
    Args:
        prev_frame: Previous video frame
        curr_frame: Current video frame
        prev_transform: Previous transformation matrix
        
    Returns:
        Stabilized frame and current transformation matrix
    """
    try:
        # Convert frames to grayscale
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # Detect feature points (use a lower threshold to detect more points)
        prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, 
                                        minDistance=30, blockSize=3)
        
        if prev_pts is None or len(prev_pts) < 4:
            # Not enough points to track
            return curr_frame, prev_transform
            
        # Calculate optical flow
        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None)
        
        # Select good points
        idx = np.where(status == 1)[0]
        if len(idx) < 4:
            # Not enough points were tracked successfully
            return curr_frame, prev_transform
            
        prev_good_pts = prev_pts[idx].reshape(-1, 2)
        curr_good_pts = curr_pts[idx].reshape(-1, 2)
        
        # Find transformation matrix
        transform_matrix, inliers = cv2.estimateAffinePartial2D(
            prev_good_pts, curr_good_pts, method=cv2.RANSAC, ransacReprojThreshold=3.0
        )
        
        if transform_matrix is None:
            return curr_frame, prev_transform
            
        # Extract translation
        dx = transform_matrix[0, 2]
        dy = transform_matrix[1, 2]
        
        # Extract rotation angle
        da = np.arctan2(transform_matrix[1, 0], transform_matrix[0, 0])
        
        # Limit transformation for smoothness with adaptive scaling
        # For large movements, apply less stabilization to avoid edge artifacts
        movement_magnitude = np.sqrt(dx*dx + dy*dy)
        scale_rotation = 0.1
        
        # Scale translation stabilization inversely with movement
        if movement_magnitude > 30:
            scale_translation = 0.05  # Less stabilization for large movements
        elif movement_magnitude > 15:
            scale_translation = 0.1  # Medium stabilization for moderate movements
        else:
            scale_translation = 0.2  # More stabilization for small movements
        
        # Build new transformation matrix
        transform_matrix[0, 0] = np.cos(da * scale_rotation)
        transform_matrix[0, 1] = -np.sin(da * scale_rotation)
        transform_matrix[1, 0] = np.sin(da * scale_rotation) 
        transform_matrix[1, 1] = np.cos(da * scale_rotation)
        transform_matrix[0, 2] = dx * scale_translation
        transform_matrix[1, 2] = dy * scale_translation
        
        # Apply stabilizing transform
        height, width = curr_frame.shape[:2]
        stabilized_frame = cv2.warpAffine(curr_frame, transform_matrix, (width, height))
        
        return stabilized_frame, transform_matrix
        
    except Exception as e:
        logger.error(f"Error in frame stabilization: {e}")
        # Return original frame on error
        return curr_frame, prev_transform

def stabilize_video(frames: Optional[List[np.ndarray]] = None, 
                   frame: Optional[np.ndarray] = None, 
                   prev_frame: Optional[np.ndarray] = None, 
                   prev_transform: Optional[np.ndarray] = None,
                   smoothing_window: int = 30) -> Union[List[np.ndarray], Tuple[np.ndarray, Optional[np.ndarray]]]:
    """
    Stabilize video input. Can work in two modes:
    1. Process a batch of frames (frames parameter)
    2. Process a single frame with reference to previous frame and transform
    
    Args:
        frames: List of frames to stabilize
        frame: Current frame to stabilize
        prev_frame: Previous frame used for stabilization
        prev_transform: Previous transformation matrix
        smoothing_window: Size of smoothing window (larger = more stable, more cropping)
        
    Returns:
        Stabilized frames or (stabilized_frame, transform) tuple
    """
    try:
        if frames is not None:
            # Batch processing mode
            if len(frames) < 2:
                return frames
                
            stabilized_frames = [frames[0]]
            prev_frame = frames[0]
            prev_transform = None
            
            for i in range(1, len(frames)):
                stabilized, prev_transform = stabilize_frame(prev_frame, frames[i], prev_transform)
                stabilized_frames.append(stabilized)
                prev_frame = frames[i]
                
            return stabilized_frames
            
        elif frame is not None and prev_frame is not None:
            # Single frame processing mode
            return stabilize_frame(prev_frame, frame, prev_transform)
        else:
            # Invalid parameters
            if frame is not None:
                return frame, None
            return None, None
    except Exception as e:
        logger.error(f"Error in video stabilization: {e}")
        if frames is not None:
            return frames
        elif frame is not None:
            return frame, None
        return None, None

def get_video_properties(cap: cv2.VideoCapture) -> Tuple[int, int, float]:
    """
    Get basic properties of a video capture.
    
    Args:
        cap: OpenCV VideoCapture object
        
    Returns:
        Tuple of (width, height, fps)
    """
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    return width, height, fps

def get_available_cameras() -> Dict[int, str]:
    """
    List available camera devices.
    
    Returns:
        Dictionary mapping device indices to descriptive names
    """
    available_cameras = {}
    for i in range(10):  # Try first 10 indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Try to get camera name (may not work on all systems)
            name = f"Camera {i}"
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            name += f" ({width}x{height})"
            available_cameras[i] = name
            cap.release()
    return available_cameras

class VirtualCameraOutput:
    def __init__(self, width: int = 1280, height: int = 720, fps: int = 24, device_index: int = 0):
        """
        Initialize a virtual camera output
        
        Args:
            width: Output width
            height: Output height
            fps: Output frame rate
            device_index: Device index (v4l2loopback device on Linux)
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.device_index = device_index
        self.cam = None
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize the virtual camera.
        
        Returns:
            True if initialization succeeded, False otherwise
        """
        if not VIRTUAL_CAM_AVAILABLE:
            logger.warning("PyVirtualCam not available. Virtual camera output disabled.")
            return False
            
        try:
            # Different initialization based on OS
            if IS_WINDOWS:
                # Windows supports different backends
                try:
                    # Try Unity capture backend first for better compatibility
                    self.cam = pyvirtualcam.Camera(
                        width=self.width, height=self.height, fps=self.fps,
                        backend='unitycapture'
                    )
                    logger.info(f"Created virtual camera with Unity Capture backend")
                except Exception as e:
                    logger.info(f"Unity Capture backend failed, trying OBS: {e}")
                    # Fall back to OBS backend
                    try:
                        self.cam = pyvirtualcam.Camera(
                            width=self.width, height=self.height, fps=self.fps,
                            backend='obs'
                        )
                        logger.info(f"Created virtual camera with OBS backend")
                    except Exception as e_obs:
                        # Last resort: try any available backend
                        logger.info(f"OBS backend failed, trying any available: {e_obs}")
                        self.cam = pyvirtualcam.Camera(
                            width=self.width, height=self.height, fps=self.fps
                        )
                        logger.info(f"Created virtual camera with auto-selected backend")
                
            elif IS_LINUX:
                # On Linux with v4l2loopback
                self.cam = pyvirtualcam.Camera(
                    width=self.width, height=self.height, fps=self.fps,
                    device=f'/dev/video{self.device_index}'
                )
                logger.info(f"Created virtual camera on /dev/video{self.device_index}")
            
            elif IS_MAC:
                # On macOS
                self.cam = pyvirtualcam.Camera(
                    width=self.width, height=self.height, fps=self.fps
                )
                logger.info(f"Created virtual camera on macOS")
            
            else:
                # Generic initialization for other platforms
                self.cam = pyvirtualcam.Camera(
                    width=self.width, height=self.height, fps=self.fps
                )
                logger.info(f"Created virtual camera (generic)")
            
            self.is_initialized = True
            logger.info(f"Virtual camera initialized: {self.width}x{self.height} @ {self.fps}fps")
            logger.info(f"Virtual camera device: {self.cam.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize virtual camera: {e}")
            self.is_initialized = False
            return False
            
    def send_frame(self, frame: np.ndarray) -> bool:
        """
        Send a frame to the virtual camera.
        
        Args:
            frame: BGR frame to send
            
        Returns:
            True if frame was sent, False otherwise
        """
        if not self.is_initialized or self.cam is None:
            return False
            
        try:
            # Convert BGR (OpenCV) to RGB (pyvirtualcam)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize if dimensions don't match
            if frame_rgb.shape[1] != self.width or frame_rgb.shape[0] != self.height:
                frame_rgb = cv2.resize(frame_rgb, (self.width, self.height))
                
            # Send frame
            self.cam.send(frame_rgb)
            return True
            
        except Exception as e:
            logger.error(f"Error sending frame to virtual camera: {e}")
            return False
            
    def close(self) -> None:
        """Close the virtual camera."""
        if self.cam is not None:
            try:
                self.cam.close()
                logger.info("Virtual camera closed")
            except Exception as e:
                logger.error(f"Error closing virtual camera: {e}")
        
        self.is_initialized = False
        self.cam = None

def create_virtual_camera_output(width: int = 1280, height: int = 720, 
                               fps: int = 24, device_index: int = 0) -> VirtualCameraOutput:
    """
    Create and initialize a virtual camera output.
    
    Args:
        width: Output width
        height: Output height
        fps: Output frame rate
        device_index: Device index (for v4l2loopback on Linux)
        
    Returns:
        Initialized VirtualCameraOutput instance or None if failed
    """
    # Print OS-specific installation instructions if PyVirtualCam is not available
    if not VIRTUAL_CAM_AVAILABLE:
        if IS_WINDOWS:
            logger.warning("Virtual camera requires PyVirtualCam. Install with: pip install pyvirtualcam")
            logger.warning("For Windows, you also need to install one of these virtual camera drivers:")
            logger.warning("- OBS Virtual Camera (install OBS Studio)")
            logger.warning("- Unity Capture (https://github.com/schellingb/UnityCapture)")
        elif IS_LINUX:
            logger.warning("Virtual camera requires PyVirtualCam. Install with: pip install pyvirtualcam")
            logger.warning("For Linux, you also need v4l2loopback:")
            logger.warning("- Ubuntu/Debian: sudo apt install v4l2loopback-dkms")
            logger.warning("- Fedora: sudo dnf install v4l2loopback")
            logger.warning("Load the module with: sudo modprobe v4l2loopback")
        elif IS_MAC:
            logger.warning("Virtual camera requires PyVirtualCam. Install with: pip install pyvirtualcam")
            logger.warning("For macOS, you also need to install a virtual camera driver:")
            logger.warning("- OBS Virtual Camera (install OBS Studio)")
        return None

    output = VirtualCameraOutput(width, height, fps, device_index)
    if output.initialize():
        return output
    return None

def apply_text_overlay(frame: np.ndarray, text: str, position: Tuple[int, int], 
                      font_scale: float = 0.7, color: Tuple[int, int, int] = (255, 255, 255), 
                      thickness: int = 2) -> np.ndarray:
    """
    Add text overlay to a frame.
    
    Args:
        frame: Input frame
        text: Text to add
        position: (x, y) coordinates
        font_scale: Font size scale
        color: Text color (BGR)
        thickness: Text thickness
        
    Returns:
        Frame with text overlay
    """
    return cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                     font_scale, color, thickness)

def apply_rectangle_overlay(frame: np.ndarray, top_left: Tuple[int, int], 
                          bottom_right: Tuple[int, int], 
                          color: Tuple[int, int, int] = (0, 255, 0), 
                          thickness: int = 2) -> np.ndarray:
    """
    Add a rectangle overlay to a frame.
    
    Args:
        frame: Input frame
        top_left: (x, y) coordinates of top-left corner
        bottom_right: (x, y) coordinates of bottom-right corner
        color: Rectangle color (BGR)
        thickness: Line thickness (-1 for filled rectangle)
        
    Returns:
        Frame with rectangle overlay
    """
    return cv2.rectangle(frame, top_left, bottom_right, color, thickness)

def create_hud_overlay(frame: np.ndarray, alpha: float = 0.7) -> np.ndarray:
    """
    Create a semi-transparent HUD overlay base.
    
    Args:
        frame: Input frame
        alpha: Transparency factor (0.0-1.0)
        
    Returns:
        Frame with semi-transparent overlay
    """
    overlay = frame.copy()
    height, width = frame.shape[:2]
    
    # Top bar
    cv2.rectangle(overlay, (0, 0), (width, 60), (0, 0, 0), -1)
    # Bottom bar
    cv2.rectangle(overlay, (0, height-40), (width, height), (0, 0, 0), -1)
    
    # Blend overlay with original frame
    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

def calculate_fps(start_time: float, frame_count: int) -> float:
    """
    Calculate frames per second.
    
    Args:
        start_time: Starting time in seconds
        frame_count: Number of frames processed
        
    Returns:
        FPS value
    """
    elapsed_time = time.time() - start_time
    return frame_count / elapsed_time if elapsed_time > 0 else 0