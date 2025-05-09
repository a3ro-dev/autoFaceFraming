import cv2
import numpy as np
import time
import yaml
import os
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
import threading

from .face_detector import FaceDetector
from .tracker import Tracker
from .utils.video_utils import stabilize_video, create_virtual_camera_output, IS_WINDOWS, IS_LINUX, IS_MAC

class CameraStream:
    def __init__(self, width: Union[int, Dict[str, int]] = 1280, 
                height: int = 720, 
                fps: int = 24,
                camera_index: int = -1):
        """
        Initialize camera stream with specified parameters.
        
        Args:
            width: Camera width resolution or dict with width and height
            height: Camera height resolution
            fps: Frame rate
            camera_index: Camera index to use (-1 for auto-detect)
        """
        # Set resolution and frame rate
        if isinstance(width, dict) and 'width' in width and 'height' in width:
            self.width = width['width']
            self.height = width['height']
        else:
            self.width = width
            self.height = height
        self.fps = fps
        
        # Initialize camera
        self.cap = self._initialize_camera(camera_index)
            
        # Initialize components
        self.face_detector = FaceDetector(detector_type='haar')  # Can be changed to 'dnn'
        self.tracker = Tracker(smooth_factor=0.05)  # More smoothing
        
        # For stabilization
        self.prev_frame = None
        self.prev_transform = None
        
        # Virtual camera output
        self.virtual_cam = None
        
        # For FPS calculation
        self.frame_counter = 0
        self.start_time = time.time()
        self.fps_actual = 0
        self.last_fps_update = time.time()
        
        # For system information
        self.system_info = self._init_system_info()
        self.last_system_info_update = time.time()
        
        # Frame rate limiter for consistent fps
        self.frame_time = 1.0 / self.fps
        self.last_frame_time = time.time()
        
        # Running flag
        self.is_running = False
        
        # Threading support
        self.processing_thread = None
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.processed_frame = None
    
    def _init_system_info(self) -> Dict[str, Any]:
        """Initialize system information dictionary"""
        return {
            'os': platform.system() + ' ' + platform.release(),
            'processor': platform.processor(),
            'cpu_percent': 0,
            'memory_percent': 0,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
        }
    
    def _initialize_camera(self, camera_index: int) -> cv2.VideoCapture:
        """
        Initialize the camera by trying different indices or device paths.
        
        Args:
            camera_index: Camera index to use (-1 for auto-detect)
            
        Returns:
            Initialized camera capture object
            
        Raises:
            ValueError: If no camera could be opened
        """
        cap = None
        
        # If camera index is specified, try only that one
        if camera_index >= 0:
            print(f"Trying to open camera at index {camera_index}...")
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                print(f"Successfully opened camera at index {camera_index}")
                # Configure camera properties
                self._configure_camera(cap)
                return cap
            else:
                print(f"Failed to open camera at index {camera_index}")
                
        # Try to find an available camera by checking multiple indices
        camera_indices = list(range(10))  # Try indices 0-9
        
        for idx in camera_indices:
            print(f"Trying to open camera at index {idx}...")
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                print(f"Successfully opened camera at index {idx}")
                # Configure camera properties
                self._configure_camera(cap)
                return cap
        
        # If no camera was found, try device paths directly
        for i in range(10):
            device_path = f"/dev/video{i}"
            if os.path.exists(device_path):
                print(f"Trying to open camera at {device_path}...")
                cap = cv2.VideoCapture(device_path)
                if cap.isOpened():
                    print(f"Successfully opened camera at {device_path}")
                    # Configure camera properties
                    self._configure_camera(cap)
                    return cap
        
        # Check if camera opened successfully
        raise ValueError("Error: Could not open video capture device. Make sure your camera is connected and not in use by another application.")
    
    def _configure_camera(self, cap: cv2.VideoCapture) -> None:
        """
        Configure camera properties.
        
        Args:
            cap: OpenCV VideoCapture object
        """
        # Force camera properties to ensure requested resolution and fps
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Print actual camera properties
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera opened with resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")
        
    def initialize_virtual_camera(self) -> bool:
        """
        Initialize virtual camera output.
        
        Returns:
            True if successful, False otherwise
        """
        self.virtual_cam = create_virtual_camera_output(
            width=self.width, height=self.height, fps=self.fps
        )
        
        return self.virtual_cam is not None and self.virtual_cam.is_initialized
        
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame from the camera and limit to target frame rate.
        
        Returns:
            Frame from camera or None if read failed
        """
        # Calculate time since last frame
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        
        # Wait if we're going faster than our target frame rate
        if elapsed < self.frame_time:
            time.sleep(self.frame_time - elapsed)
            
        # Record new frame time
        self.last_frame_time = time.time()
        
        # Get the frame
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame from camera")
            return None
            
        # If the camera returns a frame with incorrect dimensions, resize it
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
            
        return frame
        
    def update_system_info(self) -> None:
        """Update system information for HUD"""
        current_time = time.time()
        # Only update system info every second to avoid performance impact
        if current_time - self.last_system_info_update < 1.0:
            return
            
        try:
            self.system_info = {
                'os': platform.system() + ' ' + platform.release(),
                'processor': platform.processor(),
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
            }
        except Exception as e:
            print(f"Error updating system info: {e}")
            # Keep using old values if update fails
            
        self.last_system_info_update = current_time
        
    def draw_enhanced_hud(self, frame: np.ndarray, 
                        faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Draw an enhanced HUD with system info and face tracking details.
        
        Args:
            frame: The video frame to draw HUD on
            faces: List of detected face coordinates
            
        Returns:
            Frame with HUD overlay
        """
        # Update system info
        self.update_system_info()
        
        # Create semi-transparent overlay for the HUD
        overlay = frame.copy()
        
        # Draw top bar
        cv2.rectangle(overlay, (0, 0), (self.width, 60), (0, 0, 0), -1)
        # Draw bottom bar
        cv2.rectangle(overlay, (0, self.height-40), (self.width, self.height), (0, 0, 0), -1)
        
        # Add system info to top bar
        cv2.putText(overlay, f"OS: {self.system_info['os']}", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(overlay, f"CPU: {self.system_info['cpu_percent']}% | RAM: {self.system_info['memory_percent']}%", 
                   (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add time and FPS to right side of top bar
        timestamp_text = self.system_info['timestamp']
        timestamp_size = cv2.getTextSize(timestamp_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.putText(overlay, timestamp_text, 
                   (self.width - timestamp_size[0] - 10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        fps_text = f"FPS: {self.fps_actual:.1f}"
        fps_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.putText(overlay, fps_text, 
                   (self.width - fps_size[0] - 10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                   (255, 255, 0) if self.fps_actual >= 20 else (0, 0, 255), 2)
        
        # Add face tracking info to bottom bar
        if len(faces) > 0:
            cv2.putText(overlay, f"Faces detected: {len(faces)}", (10, self.height-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Get primary face dimensions
            primary_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = primary_face
            face_area = w * h
            frame_area = self.width * self.height
            face_percentage = (face_area / frame_area) * 100
            
            cv2.putText(overlay, f"Face size: {face_percentage:.1f}% of frame", 
                       (250, self.height-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(overlay, "No faces detected", (10, self.height-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Draw small logo
        logo_text = "AUTO FACE FRAMING"
        logo_size = cv2.getTextSize(logo_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.putText(overlay, logo_text, 
                   (self.width - logo_size[0] - 10, self.height-15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
                   
        # Blend the overlay with the original frame
        alpha = 0.7  # Transparency factor
        frame_with_hud = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        return frame_with_hud
        
    def update_fps(self) -> None:
        """Update FPS calculation"""
        self.frame_counter += 1
        elapsed_time = time.time() - self.last_fps_update
        
        # Update FPS every second
        if elapsed_time > 1.0:
            self.fps_actual = self.frame_counter / elapsed_time
            self.frame_counter = 0
            self.last_fps_update = time.time()
        
    def display_frame(self, frame: np.ndarray, show_window: bool = False) -> None:
        """
        Display frame on virtual camera and/or window.
        
        Args:
            frame: Frame to display
            show_window: Whether to show a window
        """
        if frame is None:
            return
            
        # Update FPS counter
        self.update_fps()
        
        # Send to virtual camera if available
        if self.virtual_cam and self.virtual_cam.is_initialized:
            try:
                self.virtual_cam.send_frame(frame)
            except Exception as e:
                print(f"Error sending frame to virtual camera: {e}")
        
        # Show window if requested and if OpenCV has GUI support
        if show_window:
            try:
                cv2.imshow("Auto Face Framing", frame)
                cv2.waitKey(1)  # Process events
            except Exception as e:
                # Silently ignore GUI errors - OpenCV probably built without GUI support
                pass
    
    def process_frame(self, frame: np.ndarray, show_debug: bool = True) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
        """
        Process a single frame with face detection and tracking.
        
        Args:
            frame: Input frame
            show_debug: Whether to show debug info
            
        Returns:
            Tuple of (processed frame, detected faces)
        """
        if frame is None:
            return None, []
            
        try:
            # Detect faces in the frame
            faces = self.face_detector.detect(frame)
            
            # Track faces and apply framing
            framed_frame = self.tracker.track(frame, faces)
            
            # Add debug visualization if requested
            if show_debug:
                # Draw face rectangles on a copy of the original frame
                debug_frame = self.face_detector.draw_faces(framed_frame, faces)
                
                # Add HUD overlay
                framed_frame = self.draw_enhanced_hud(debug_frame, faces)
            
            return framed_frame, faces
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            import traceback
            traceback.print_exc()
            return frame, []  # Return original frame if processing fails
    
    def process_frames_thread(self, show_debug: bool = True, virtual_output: bool = True, show_window: bool = False) -> None:
        """
        Process frames in a separate thread.
        
        Args:
            show_debug: Whether to show debug info
            virtual_output: Whether to use virtual camera output
            show_window: Whether to show preview window
        """
        while self.is_running:
            # Get a frame
            frame = self.get_frame()
            
            if frame is not None:
                # Update the current frame
                with self.frame_lock:
                    self.current_frame = frame
                
                # Process the frame
                processed_frame, faces = self.process_frame(frame, show_debug)
                
                # Update the processed frame
                with self.frame_lock:
                    self.processed_frame = processed_frame
                
                # Display the frame
                self.display_frame(processed_frame, show_window=show_window)
            
            # Check for exit key only if window is shown
            if show_window:
                try:
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.is_running = False
                        break
                except:
                    # If waitKey fails, OpenCV was built without GUI support
                    pass
    
    def start_stream(self, show_debug: bool = True, virtual_output: bool = True, show_window: bool = False) -> None:
        """
        Start the video stream processing loop.
        
        Args:
            show_debug: Whether to show debug info
            virtual_output: Whether to enable virtual camera output
            show_window: Whether to show preview window
        """
        # Initialize virtual camera if requested
        if virtual_output:
            self.initialize_virtual_camera()
        
        print("Starting video stream processing...")
        print(f"Debug overlay: {'Enabled' if show_debug else 'Disabled'}")
        print(f"Virtual camera: {'Enabled' if virtual_output and self.virtual_cam and self.virtual_cam.is_initialized else 'Disabled'}")
        print(f"Preview window: {'Enabled' if show_window else 'Disabled'}")
        
        # Set running flag
        self.is_running = True
        
        # Start processing in the main thread
        try:
            while self.is_running:
                # Get a frame
                frame = self.get_frame()
                
                if frame is None:
                    print("No frame received, retrying...")
                    time.sleep(0.1)
                    continue
                
                # Process the frame
                processed_frame, faces = self.process_frame(frame, show_debug)
                
                # Display the frame
                self.display_frame(processed_frame, show_window=show_window)
                
                # Check for exit key only if window is shown
                if show_window:
                    try:
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    except:
                        # If waitKey fails, OpenCV was built without GUI support
                        pass
                    
        except KeyboardInterrupt:
            print("Stream interrupted by user")
        except Exception as e:
            print(f"Error in stream processing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up
            self.is_running = False
            # Only try to destroy windows if requested to show them
            if show_window:
                try:
                    cv2.destroyAllWindows()
                except:
                    pass  # Ignore errors if OpenCV was built without GUI support
    
    def start_threaded(self, show_debug: bool = True, virtual_output: bool = True, show_window: bool = False) -> bool:
        """
        Start video processing in a separate thread.
        
        Args:
            show_debug: Whether to show debug info
            virtual_output: Whether to enable virtual camera output
            show_window: Whether to show preview window
            
        Returns:
            True if thread started successfully, False otherwise
        """
        # Initialize virtual camera if requested
        if virtual_output:
            self.initialize_virtual_camera()
        
        # Set running flag
        self.is_running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self.process_frames_thread,
            args=(show_debug, virtual_output, show_window)
        )
        self.processing_thread.daemon = True  # Thread will close when main program exits
        
        try:
            self.processing_thread.start()
            return True
        except Exception as e:
            print(f"Error starting processing thread: {e}")
            self.is_running = False
            return False
        
    def release(self) -> None:
        """Release resources"""
        self.is_running = False
        
        # Wait for thread to finish if it exists
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        
        # Release camera
        if self.cap and self.cap.isOpened():
            self.cap.release()
            
        # Close virtual camera
        if self.virtual_cam:
            self.virtual_cam.close()
            
        # Close any open windows - do this safely
        try:
            cv2.destroyAllWindows()
        except:
            pass  # Ignore errors if OpenCV was built without GUI support
        
        print("Camera resources released")


def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary or None if loading failed
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                
                # Just log the filename and parent directory for cleaner output
                config_display = f"{os.path.basename(os.path.dirname(config_path))}/{os.path.basename(config_path)}"
                config_type = "user" if "autoFaceFraming/config" not in config_path else "default"
                print(f"Loaded {config_type} configuration from {config_display}")
                return config
        else:
            print(f"Configuration file not found: {config_path}")
            return None
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None

if __name__ == "__main__":
    # Try to load config
    config = load_config('config/settings.yaml')
    
    if config:
        camera_stream = CameraStream(
            width=config['camera']['resolution'],
            height=config['camera']['resolution']['height'],
            fps=config['camera']['frame_rate']
        )
    else:
        # Fallback to default settings
        camera_stream = CameraStream()
        
    camera_stream.start_stream()