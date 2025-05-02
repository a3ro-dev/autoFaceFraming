# Auto Face Framing Tutorial

**By Akshat Kushwaha | [@a3rodev](https://twitter.com/a3rodev) | [GitHub](https://github.com/a3ro-dev)**

This tutorial will guide you through the process of setting up and using Auto Face Framing, a smart camera framing system that automatically detects and tracks faces in real-time.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Advanced Configuration](#advanced-configuration)
4. [Use Cases](#use-cases)
5. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

Before installing Auto Face Framing, make sure you have:

- Python 3.8 or newer
- A webcam or other camera device
- Virtual camera driver (platform-specific, see below)

### Installing from PyPI

1. Install the package using pip:
   ```bash
   pip install auto-face-framing
   ```

2. Install virtual camera driver for your operating system:

   **For Linux:**
   ```bash
   # For Ubuntu/Debian
   sudo apt install v4l2loopback-dkms
   
   # For Fedora
   sudo dnf install v4l2loopback
   
   # Then load the module
   sudo modprobe v4l2loopback
   ```

   **For Windows:**
   Install one of these virtual camera drivers:
   - OBS Virtual Camera (included with [OBS Studio](https://obsproject.com/))
   - [Unity Capture](https://github.com/schellingb/UnityCapture)

   **For macOS:**
   - OBS Virtual Camera (included with [OBS Studio](https://obsproject.com/))

## Basic Usage

### Starting the Application

After installation, you can start Auto Face Framing with the command:

```bash
start-face-framing
```

By default, this will:
- Automatically detect available cameras
- Start face tracking with debug overlay
- Create a virtual camera output
- Use the default configuration settings

### Command Line Options

You can customize the behavior with command line options:

```bash
start-face-framing --resolution 1920x1080 --fps 30
```

Available options:
- `--config PATH`: Use a custom configuration file
- `--no-virtual`: Disable virtual camera output
- `--resolution WIDTHxHEIGHT`: Set camera resolution
- `--fps FPS`: Set frame rate
- `--no-window`: Hide the preview window
- `--verbose`: Enable detailed logging
- `--version`: Show version information
- `--camera-index N`: Specify a camera index (0, 1, 2, etc.)

### Using with Video Conference Apps

After starting Auto Face Framing:

1. Open your video conferencing application (Zoom, Meet, Teams, etc.)
2. In the camera/video settings, select the virtual camera:
   - **Windows**: Select "OBS Virtual Camera" or "Unity Virtual Camera"
   - **Linux**: Select "v4l2loopback" or similar virtual device
   - **macOS**: Select "OBS Virtual Camera"
3. Your face will now be automatically tracked and centered during your call

## Advanced Configuration

### Creating a Custom Configuration File

You can create a custom YAML configuration file with your preferred settings:

```yaml
# my-config.yaml
camera:
  resolution:
    width: 1920
    height: 1080
  frame_rate: 30
  camera_index: 0  # Use specific camera

face_detection:
  detector_type: "dnn"  # Use more accurate DNN detection
  confidence_threshold: 0.6
  
tracking:
  smooth_factor: 0.1  # More responsive tracking
  adaptive_smoothing: true
  
advanced:
  use_threading: true  # Enable threaded processing for better performance
```

Save this file and use it with:

```bash
start-face-framing --config my-config.yaml
```

### Switching Detection Methods

Auto Face Framing supports two face detection methods:

1. **Haar Cascades** (Default): Faster but less accurate
   ```yaml
   face_detection:
     detector_type: "haar"
   ```

2. **DNN**: More accurate but requires more processing power
   ```yaml
   face_detection:
     detector_type: "dnn"
     confidence_threshold: 0.6  # Higher values = more confident detections
   ```

### Adjusting Tracking Smoothness

You can fine-tune how smoothly the camera follows your face:

```yaml
tracking:
  smooth_factor: 0.05  # Lower = smoother but slower (range: 0.01-0.2)
  adaptive_smoothing: true  # Adjusts based on movement magnitude
```

## Use Cases

### 1. Professional Video Calls

Perfect for maintaining a professional appearance in video conferences. Auto Face Framing will:
- Keep your face centered even if you move
- Adjust zoom level based on your distance from the camera
- Prevent distracting camera movements

### 2. Content Creation

For YouTubers, streamers, and content creators:
- Maintain proper framing without a camera operator
- Create a more polished, professional look
- Focus on your content without worrying about staying in frame

### 3. Classroom or Presentation Recording

For teachers and presenters:
- Move freely while presenting
- Maintain proper framing as you gesture or move to different parts of a whiteboard
- Ensure students/audience can always see you clearly

## Troubleshooting

### Camera Not Detected

If your camera isn't detected:

1. Check if it's connected properly
2. Try specifying the camera index directly:
   ```bash
   start-face-framing --camera-index 1
   ```
   
   Or in config.yaml:
   ```yaml
   camera:
     camera_index: 1  # Try different numbers (0, 1, 2, etc.)
   ```

3. Check if another application is using the camera (close other webcam apps)

### Virtual Camera Not Working

#### On Windows

If the virtual camera output isn't showing up:

1. Make sure you have installed a virtual camera driver:
   - OBS Studio: Launch OBS at least once to register the virtual camera
   - Unity Capture: Follow installation instructions from their GitHub page

2. If using OBS Virtual Camera, try starting and stopping it in OBS:
   - In OBS Studio, go to Tools > Virtual Camera > Start Virtual Camera
   - Then stop it and try running Auto Face Framing again

3. Check if your video conferencing app recognizes virtual cameras:
   - Some apps may require you to restart them after installing a virtual camera

#### On Linux

If the virtual camera output isn't showing up:

1. Ensure v4l2loopback is installed and loaded:
   ```bash
   sudo modprobe v4l2loopback
   ```

2. Check available video devices:
   ```bash
   ls /dev/video*
   ```

3. Verify permissions:
   ```bash
   sudo usermod -a -G video YOUR_USERNAME
   ```
   (Logout and login for changes to take effect)

#### On macOS

If the virtual camera output isn't showing up:

1. Make sure OBS is installed and you've started the virtual camera at least once
2. Restart your video conferencing application
3. Check if you need to grant permission to the virtual camera in System Preferences

### Performance Issues

If you're experiencing lag or performance issues:

1. Lower the resolution:
   ```bash
   start-face-framing --resolution 640x480
   ```

2. Enable threading in your config:
   ```yaml
   advanced:
     use_threading: true
   ```

3. Switch to Haar cascade detector for better performance:
   ```yaml
   face_detection:
     detector_type: "haar"
   ```

4. Windows-specific: Close other resource-intensive applications

---

For more information, visit: [https://github.com/a3ro-dev/autoFaceFraming](https://github.com/a3ro-dev/autoFaceFraming)

© 2025 Akshat Kushwaha | [@a3rodev](https://twitter.com/a3rodev) 