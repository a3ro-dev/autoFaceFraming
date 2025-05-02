import cv2
import numpy as np
import os
from typing import List, Tuple, Optional, Union, Dict, Any

class FaceDetector:
    def __init__(self, model_path: str = 'haarcascade_frontalface_default.xml', 
                detector_type: str = 'haar',
                confidence_threshold: float = 0.5):
        """
        Initialize face detector with specified model.
        
        Args:
            model_path: Path to face detection model file
            detector_type: Type of detector to use ('haar' or 'dnn')
            confidence_threshold: Confidence threshold for DNN detector
        """
        self.detector_type = detector_type
        self.confidence_threshold = confidence_threshold
        self.dnn_model = None
        self.face_cascade = None
        
        # DNN face detector setup
        if detector_type == 'dnn':
            # Look for DNN models in common locations
            dnn_model_paths = self._find_dnn_models()
            if dnn_model_paths:
                try:
                    prototxt_path, model_path = dnn_model_paths
                    self.dnn_model = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
                    print(f"Loaded DNN face detector model from {model_path}")
                except Exception as e:
                    print(f"Error loading DNN model: {e}")
                    print("Falling back to Haar cascade detector")
                    self.detector_type = 'haar'
            else:
                print("DNN face detection model files not found. Falling back to Haar cascade.")
                self.detector_type = 'haar'
        
        # Haar cascade setup (as primary or fallback)
        if self.detector_type == 'haar':
            # Try multiple ways to load the cascade file
            self.face_cascade = self._load_haar_cascade(model_path)
                
            # Final check to make sure we have a valid classifier
            if self.face_cascade is None or self.face_cascade.empty():
                raise ValueError(f"Error loading face cascade. Please ensure the file {model_path} exists and is accessible.")

    def _find_dnn_models(self) -> Optional[Tuple[str, str]]:
        """
        Find DNN face detection model files in common locations.
        
        Returns:
            Tuple of (prototxt_path, caffemodel_path) if found, None otherwise
        """
        # Common paths for OpenCV DNN face detection models
        potential_paths = [
            # Standard OpenCV DNN model paths
            ('/usr/share/opencv4/face_detector', '/usr/share/opencv4/face_detector'),
            ('/usr/local/share/opencv4/face_detector', '/usr/local/share/opencv4/face_detector'),
            ('/usr/share/opencv/face_detector', '/usr/share/opencv/face_detector'),
            # Local model paths
            ('models/face_detector', 'models/face_detector'),
            ('face_detector', 'face_detector'),
        ]
        
        for base_path, model_dir in potential_paths:
            prototxt_path = os.path.join(base_path, 'deploy.prototxt')
            model_path = os.path.join(model_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
            
            if os.path.exists(prototxt_path) and os.path.exists(model_path):
                return prototxt_path, model_path
        
        return None
    
    def _load_haar_cascade(self, model_path: str) -> Optional[cv2.CascadeClassifier]:
        """
        Attempt to load Haar cascade from various locations.
        
        Args:
            model_path: Path to cascade XML file
            
        Returns:
            Loaded CascadeClassifier or None if failed
        """
        cascade = None
        
        # First try using cv2.data.haarcascades path
        try:
            cascade_path = os.path.join(cv2.data.haarcascades, model_path)
            if os.path.exists(cascade_path):
                cascade = cv2.CascadeClassifier(cascade_path)
                if not cascade.empty():
                    print(f"Loaded face cascade from {cascade_path}")
                    return cascade
        except:
            pass
            
        # Try direct path
        try:
            cascade = cv2.CascadeClassifier(model_path)
            if not cascade.empty():
                print(f"Loaded face cascade from {model_path}")
                return cascade
        except:
            pass
                
        # Try to find it in standard OpenCV installation paths
        potential_paths = [
            '/usr/share/opencv4/haarcascades/' + model_path,
            '/usr/local/share/opencv4/haarcascades/' + model_path,
            '/usr/share/opencv/haarcascades/' + model_path,
            '/usr/local/share/opencv/haarcascades/' + model_path
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                cascade = cv2.CascadeClassifier(path)
                if not cascade.empty():
                    print(f"Loaded face cascade from {path}")
                    return cascade
        
        return None

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input video frame
            
        Returns:
            List of face coordinates as (x, y, w, h)
        """
        if self.detector_type == 'dnn' and self.dnn_model is not None:
            return self._detect_faces_dnn(frame)
        else:
            return self._detect_faces_haar(frame)

    def _detect_faces_dnn(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using DNN-based detector.
        
        Args:
            frame: Input video frame
            
        Returns:
            List of face coordinates as (x, y, w, h)
        """
        faces = []
        frame_height, frame_width = frame.shape[:2]
        
        try:
            # Create a blob from the image
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)), 1.0, (300, 300),
                (104.0, 177.0, 123.0), swapRB=False, crop=False
            )
            
            # Pass the blob through the network
            self.dnn_model.setInput(blob)
            detections = self.dnn_model.forward()
            
            # Process detections
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                # Filter by confidence threshold
                if confidence > self.confidence_threshold:
                    # Get bounding box coordinates
                    box = detections[0, 0, i, 3:7] * np.array([frame_width, frame_height, frame_width, frame_height])
                    x1, y1, x2, y2 = box.astype(int)
                    
                    # Convert to x, y, width, height format
                    x, y = x1, y1
                    w, h = x2 - x1, y2 - y1
                    
                    # Add to faces list
                    faces.append((x, y, w, h))
        except Exception as e:
            print(f"Error in DNN face detection: {e}")
            # Fall back to Haar in case of error
            return self._detect_faces_haar(frame)
            
        return faces

    def _detect_faces_haar(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using Haar cascade classifier.
        
        Args:
            frame: Input video frame
            
        Returns:
            List of face coordinates as (x, y, w, h)
        """
        try:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray_frame, 
                scaleFactor=1.1, 
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Convert to list of tuples if faces were detected
            if len(faces) > 0:
                return [tuple(face) for face in faces]
            return []
        except Exception as e:
            print(f"Error in Haar face detection: {e}")
            return []

    def draw_faces(self, frame: np.ndarray, 
                 faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Draw rectangles around detected faces.
        
        Args:
            frame: Input video frame
            faces: List of face coordinates (x, y, w, h)
            
        Returns:
            Frame with rectangles drawn around faces
        """
        frame_copy = frame.copy()
        for (x, y, w, h) in faces:
            # Draw face rectangle in green
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw confidence label if using DNN detector
            if self.detector_type == 'dnn':
                # We don't have confidence here, but we could add it in _detect_faces_dnn
                pass
                
        return frame_copy

    def get_face_coordinates(self, 
                            faces: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
        """
        Get coordinates of the primary (largest) face.
        
        Args:
            faces: List of face coordinates
            
        Returns:
            Primary face coordinates or None if no faces detected
        """
        if len(faces) > 0:
            # Sort by area (width * height) to find the largest face
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            return faces_sorted[0]
        return None