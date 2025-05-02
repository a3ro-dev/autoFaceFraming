import pytest
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from autoFaceFraming import __version__


def test_version():
    """Test that the version is a valid string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_import():
    """Test that main components can be imported."""
    from autoFaceFraming.face_detector import FaceDetector
    from autoFaceFraming.tracker import Tracker
    from autoFaceFraming.camera_stream import CameraStream
    
    # Just test that imports work and classes can be instantiated
    detector = FaceDetector()
    assert detector is not None
    
    tracker = Tracker()
    assert tracker is not None


@pytest.mark.skip(reason="Requires camera hardware")
def test_camera_stream():
    """Test camera stream initialization (skipped by default as it requires hardware)."""
    from autoFaceFraming.camera_stream import CameraStream
    
    # This test would be skipped in CI environments
    # But can be run manually if needed
    try:
        stream = CameraStream(width=640, height=480)
        assert stream is not None
    except ValueError:
        # Expected if no camera is available
        pass 