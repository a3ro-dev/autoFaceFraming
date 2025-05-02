import cv2
import numpy as np
from collections import deque
from typing import List, Tuple, Optional, Dict, Any, Deque, Union

class Tracker:
    def __init__(self, 
                smooth_factor: float = 0.1, 
                zoom_scale_min: float = 0.5, 
                zoom_scale_max: float = 1.5, 
                history_size: int = 30,
                adaptive_smoothing: bool = True):
        """
        Initialize the face tracker with smoothing parameters.
        
        Args:
            smooth_factor: Controls how quickly the frame adjusts to face movement (0-1)
            zoom_scale_min: Minimum zoom level when face is far
            zoom_scale_max: Maximum zoom level when face is close
            history_size: Number of frames to keep for smoothing
            adaptive_smoothing: Whether to use adaptive smoothing based on movement distance
        """
        self.smooth_factor = smooth_factor
        self.zoom_scale_min = zoom_scale_min
        self.zoom_scale_max = zoom_scale_max
        self.adaptive_smoothing = adaptive_smoothing
        
        # For smoothing with exponential weighted moving average
        self.position_history: Deque[Tuple[float, float]] = deque(maxlen=history_size)
        self.size_history: Deque[float] = deque(maxlen=history_size)
        
        # Current state
        self.current_center_x: Optional[int] = None
        self.current_center_y: Optional[int] = None
        self.current_size: Optional[int] = None
        
        # Previous state for interpolation
        self.prev_center_x: Optional[int] = None
        self.prev_center_y: Optional[int] = None
        self.prev_size: Optional[int] = None
        
        # Frame dimensions
        self.frame_width: Optional[int] = None
        self.frame_height: Optional[int] = None
        
        # Frame counter for low-pass filtering
        self.frame_counter: int = 0
        
        # No-face detection counter
        self.no_face_counter: int = 0
        self.max_no_face_frames: int = 30  # How many frames to wait before relaxing tracking
        
        # Tracking status flags
        self.status: Dict[str, Any] = {
            "tracking": False,
            "confidence": 0.0,
            "lost_tracking_frames": 0,
            "stable": False
        }
        
    def configure(self, **kwargs) -> None:
        """
        Update tracker configuration parameters.
        
        Args:
            **kwargs: Parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                print(f"Tracker parameter {key} set to {value}")
    
    def reset(self) -> None:
        """Reset tracking state"""
        self.position_history.clear()
        self.size_history.clear()
        self.current_center_x = None
        self.current_center_y = None
        self.current_size = None
        self.prev_center_x = None
        self.prev_center_y = None
        self.prev_size = None
        self.frame_counter = 0
        self.no_face_counter = 0
        self.status["tracking"] = False
        self.status["confidence"] = 0.0
        self.status["lost_tracking_frames"] = 0
        self.status["stable"] = False
        
    def track(self, frame: np.ndarray, 
             faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Track the detected face and adjust frame accordingly.
        
        Args:
            frame: The input video frame
            faces: List of face coordinates in format (x, y, w, h)
            
        Returns:
            The adjusted frame with the face centered and properly zoomed
        """
        try:
            self.frame_height, self.frame_width = frame.shape[:2]
            self.frame_counter += 1
            
            # Initialize current position if needed
            if self.current_center_x is None:
                self._initialize_tracking_state()
                
            # If no faces detected, handle gracefully
            if len(faces) == 0:
                return self._handle_no_faces(frame)
                
            # Get the largest face (closest to the camera)
            face = max(faces, key=lambda f: f[2] * f[3])
            self._update_tracking_with_face(face)
            
            # Apply the framing to the image
            return self._apply_framing(frame)
            
        except Exception as e:
            print(f"Error in face tracking: {e}")
            # In case of error, return the original frame
            return frame
    
    def _initialize_tracking_state(self) -> None:
        """Initialize tracking state variables"""
        self.current_center_x = self.frame_width // 2
        self.current_center_y = self.frame_height // 2
        self.current_size = min(self.frame_width, self.frame_height) // 2
        self.prev_center_x = self.current_center_x
        self.prev_center_y = self.current_center_y
        self.prev_size = self.current_size
    
    def _handle_no_faces(self, frame: np.ndarray) -> np.ndarray:
        """
        Handle frame when no faces are detected.
        
        Args:
            frame: The input video frame
            
        Returns:
            The adjusted frame
        """
        # Increment no-face counter
        self.no_face_counter += 1
        self.status["lost_tracking_frames"] = self.no_face_counter
        
        # If we lost face for too long, start relaxing back to center
        if self.no_face_counter > self.max_no_face_frames:
            # Gradually return to center with increasing speed based on how long tracking is lost
            relax_factor = min(0.01 * (self.no_face_counter - self.max_no_face_frames), 0.1)
            
            # Move toward center
            center_x = self.frame_width // 2
            center_y = self.frame_height // 2
            default_size = min(self.frame_width, self.frame_height) // 2
            
            # Apply relaxation
            self.current_center_x = int((1 - relax_factor) * self.current_center_x + relax_factor * center_x)
            self.current_center_y = int((1 - relax_factor) * self.current_center_y + relax_factor * center_y)
            self.current_size = int((1 - relax_factor) * self.current_size + relax_factor * default_size)
            
            self.status["confidence"] = max(0.0, 1.0 - (self.no_face_counter - self.max_no_face_frames) / 30.0)
        else:
            # For short duration, maintain last position
            self.status["confidence"] = max(0.0, 1.0 - self.no_face_counter / self.max_no_face_frames)
        
        # Update status
        self.status["tracking"] = self.no_face_counter < self.max_no_face_frames * 2
        
        # Apply framing with current settings
        return self._apply_framing(frame)
    
    def _update_tracking_with_face(self, face: Tuple[int, int, int, int]) -> None:
        """
        Update tracking state with a detected face.
        
        Args:
            face: Face coordinates (x, y, w, h)
        """
        x, y, w, h = face
        
        # Reset no-face counter since we found a face
        self.no_face_counter = 0
        self.status["tracking"] = True
        self.status["confidence"] = 1.0
        self.status["lost_tracking_frames"] = 0
        
        # Calculate face center and size
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        face_size = max(w, h)
        
        # Update position history
        self.position_history.append((face_center_x, face_center_y))
        self.size_history.append(face_size)
        
        # Calculate smoothed position using exponential moving average with more weight on recent frames
        smoothed_center_x, smoothed_center_y = self._calculate_smoothed_position()
        smoothed_size = self._calculate_smoothed_size()
        
        # Save previous state
        self.prev_center_x = self.current_center_x
        self.prev_center_y = self.current_center_y
        self.prev_size = self.current_size
        
        # Apply adaptive smoothing if enabled
        if self.adaptive_smoothing:
            self._update_with_adaptive_smoothing(smoothed_center_x, smoothed_center_y, smoothed_size)
        else:
            self._update_with_fixed_smoothing(smoothed_center_x, smoothed_center_y, smoothed_size)
            
        # Update stability status
        distance_from_prev = np.sqrt((self.current_center_x - self.prev_center_x)**2 + 
                                   (self.current_center_y - self.prev_center_y)**2)
        self.status["stable"] = distance_from_prev < 5  # Stable if movement is small
    
    def _update_with_adaptive_smoothing(self, 
                                       smoothed_center_x: float, 
                                       smoothed_center_y: float, 
                                       smoothed_size: float) -> None:
        """
        Update tracking with adaptive smoothing based on movement distance.
        
        Args:
            smoothed_center_x: Smoothed center x coordinate
            smoothed_center_y: Smoothed center y coordinate
            smoothed_size: Smoothed face size
        """
        # Calculate distance moved
        distance_moved = np.sqrt((smoothed_center_x - self.current_center_x)**2 + 
                               (smoothed_center_y - self.current_center_y)**2)
        
        # Adjust smoothing factor based on movement distance
        adaptive_smooth = self.smooth_factor
        
        if distance_moved > 50:  # Large movement
            adaptive_smooth = self.smooth_factor * 0.5  # Slower response to large movements
        elif distance_moved < 10:  # Small movement
            adaptive_smooth = self.smooth_factor * 1.5  # Quicker response to small adjustments
        
        # Update current position with adaptive smoothing
        self.current_center_x = int((1 - adaptive_smooth) * self.current_center_x + 
                                  adaptive_smooth * smoothed_center_x)
        self.current_center_y = int((1 - adaptive_smooth) * self.current_center_y + 
                                  adaptive_smooth * smoothed_center_y)
        self.current_size = int((1 - self.smooth_factor * 0.5) * self.current_size + 
                              self.smooth_factor * 0.5 * smoothed_size)  # Slower zoom changes
    
    def _update_with_fixed_smoothing(self, 
                                    smoothed_center_x: float, 
                                    smoothed_center_y: float, 
                                    smoothed_size: float) -> None:
        """
        Update tracking with fixed smoothing factor.
        
        Args:
            smoothed_center_x: Smoothed center x coordinate
            smoothed_center_y: Smoothed center y coordinate
            smoothed_size: Smoothed face size
        """
        # Update current position with fixed smoothing
        self.current_center_x = int((1 - self.smooth_factor) * self.current_center_x + 
                                  self.smooth_factor * smoothed_center_x)
        self.current_center_y = int((1 - self.smooth_factor) * self.current_center_y + 
                                  self.smooth_factor * smoothed_center_y)
        self.current_size = int((1 - self.smooth_factor * 0.5) * self.current_size + 
                              self.smooth_factor * 0.5 * smoothed_size)
        
    def _calculate_smoothed_position(self) -> Tuple[float, float]:
        """
        Calculate smoothed position from history using weighted average.
        
        Returns:
            Tuple of (smoothed_x, smoothed_y)
        """
        if not self.position_history:
            return float(self.current_center_x), float(self.current_center_y)
            
        # Apply exponential weights - more recent positions have higher weight
        positions = list(self.position_history)
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for i, (x, y) in enumerate(positions):
            # Exponential weighting - more recent values have higher weight
            weight = np.exp(i / len(positions))
            total_weight += weight
            weighted_x += x * weight
            weighted_y += y * weight
            
        return weighted_x / total_weight, weighted_y / total_weight
        
    def _calculate_smoothed_size(self) -> float:
        """
        Calculate smoothed size from history using weighted average.
        
        Returns:
            Smoothed size value
        """
        if not self.size_history:
            return float(self.current_size)
            
        # Apply exponential weights - more recent sizes have higher weight
        sizes = list(self.size_history)
        total_weight = 0
        weighted_size = 0
        
        for i, size in enumerate(sizes):
            weight = np.exp(i / len(sizes))
            total_weight += weight
            weighted_size += size * weight
            
        return weighted_size / total_weight
        
    def _apply_framing(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply zoom and centering to frame.
        
        Args:
            frame: The input video frame
            
        Returns:
            The reframed video frame
        """
        try:
            # Calculate the desired zoom scale based on face size relative to frame
            # Larger face = less zoom, smaller face = more zoom
            face_frame_ratio = self.current_size / min(self.frame_width, self.frame_height)
            zoom_factor = max(min(1.0 / face_frame_ratio * 0.5, self.zoom_scale_max), self.zoom_scale_min)
            
            # Calculate target dimensions based on zoom factor
            target_width = int(self.frame_width / zoom_factor)
            target_height = int(self.frame_height / zoom_factor)
            
            # Calculate crop coordinates centered on tracked face position
            crop_x = max(0, min(self.current_center_x - target_width // 2, 
                              self.frame_width - target_width))
            crop_y = max(0, min(self.current_center_y - target_height // 2, 
                              self.frame_height - target_height))
                              
            # Make sure we don't exceed frame boundaries
            crop_width = min(target_width, self.frame_width - crop_x)
            crop_height = min(target_height, self.frame_height - crop_y)
            
            # Ensure we have valid dimensions before cropping
            if crop_width <= 0 or crop_height <= 0:
                return frame
                
            # Crop and resize
            cropped = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
            
            # Check if cropping was successful
            if cropped.size == 0:
                print("Warning: Cropping resulted in empty frame. Returning original.")
                return frame
                
            # Use LANCZOS for high-quality resizing
            resized = cv2.resize(cropped, (self.frame_width, self.frame_height), 
                               interpolation=cv2.INTER_LANCZOS4)
            
            return resized
            
        except Exception as e:
            print(f"Framing error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to original frame if any errors occur
            return frame
    
    def get_tracking_status(self) -> Dict[str, Any]:
        """
        Get current tracking status information.
        
        Returns:
            Dictionary with tracking status details
        """
        return {
            "tracking": self.status["tracking"],
            "confidence": self.status["confidence"],
            "lost_frames": self.status["lost_tracking_frames"],
            "stable": self.status["stable"],
            "position": (self.current_center_x, self.current_center_y) if self.current_center_x else None,
            "size": self.current_size,
            "zoom_factor": (min(self.frame_width, self.frame_height) / self.current_size) 
                          if self.current_size else 1.0
        }