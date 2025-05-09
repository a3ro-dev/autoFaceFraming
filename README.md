# Auto Face Framing

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Auto Face Framing** is a Python application that creates a virtual camera output, intelligently detecting and tracking the user's face in real-time. It ensures your face remains centered and well-framed during video calls, enhancing your professional appearance. The application uses OpenCV for robust face detection and tracking.

## Overview

Tired of manually adjusting your camera during video conferences? Auto Face Framing takes care of it for you! It provides a smooth, stabilized virtual camera feed that can be used with popular video conferencing software like Zoom, Microsoft Teams, Google Meet, and more.

## Key Features

*   **Real-time Face Detection & Tracking**: Utilizes OpenCV for accurate and efficient face detection.
*   **Automatic Framing & Zoom**: Intelligently adjusts the frame and zoom level to keep your face centered and appropriately sized.
*   **Smooth Camera Movements**: Implements algorithms for smooth and natural-feeling camera adjustments.
*   **Virtual Camera Output**: Creates a virtual camera device recognized by most video conferencing applications.
*   **Cross-Platform**: Supports Windows, macOS, and Linux.
*   **Highly Configurable**: Adjust settings like resolution, FPS, framing preferences, and more via a YAML configuration file.
*   **Debug Mode**: Optional overlay to display real-time detection information and performance metrics.
*   **CLI Interface**: Easy-to-use command-line interface for starting and configuring the application.
*   **Fancy Terminal UI**: Provides an enhanced terminal experience with spinners and colored output (can be disabled).

## Project Structure

A brief overview of the project's layout:

```
autoFaceFraming/
├── autoFaceFraming/            # Main package directory
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface logic
│   ├── camera_stream.py        # Handles camera input, processing, and output
│   ├── face_detector.py        # Face detection algorithms
│   ├── tracker.py              # Face tracking logic
│   ├── config/
│   │   └── settings.yaml       # Default application settings
│   ├── models/                 # Directory for detection models
│   │   └── face_detector/
│   │       ├── deploy.prototxt # DNN model architecture
│   │       └── res10_300x300_ssd_iter_140000.caffemodel # DNN model weights
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── cli_spinner.py      # Animated spinner for CLI
│       └── video_utils.py      # Video processing utilities
├── config/                     # User-specific configuration (copied from package on first run)
│   └── settings.yaml
├── models/                     # User-specific models (copied or downloaded)
│   └── face_detector/
├── tests/                      # Unit and integration tests
│   └── ...
├── install.sh                  # Installation script for Linux/macOS
├── setup_windows.bat           # Windows setup helper script
├── requirements.txt            # Python package dependencies
├── setup.py                    # Script for packaging and distribution
├── README.md                   # This file
├── TUTORIAL.md                 # Detailed tutorial
└── LICENSE                     # Project license
```

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python**: Version 3.10+ recommended.
*   **pip**: Python package installer.
*   **Git**: For cloning the repository.

### OS-Specific Prerequisites:

*   **Windows**:
    *   A virtual camera driver. We recommend **OBS Studio** (which includes OBS Virtual Camera) or **Unity Capture**.
    *   If Python is not in your PATH, `setup_windows.bat` will attempt to add it.
*   **Linux**:
    *   `v4l2loopback` kernel module for creating virtual cameras.
        *   Debian/Ubuntu: `sudo apt install v4l2loopback-dkms`
        *   Fedora: `sudo dnf install v4l2loopback`
        *   After installation, load the module: `sudo modprobe v4l2loopback`
*   **macOS**:
    *   A virtual camera driver. We recommend **OBS Studio** (which includes OBS Virtual Camera).

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/a3ro-dev/autoFaceFraming.git
    cd autoFaceFraming
    ```

2.  **Run the Installer**:

    *   **Windows**:
        Open Command Prompt or PowerShell **as Administrator** and run:
        ```batch
        setup_windows.bat
        ```
        This script will:
        *   Attempt to add Python to your PATH if not already configured.
        *   Guide you through installing necessary Python packages.
        *   Set up the `start-face-framing.bat` convenience script.

    *   **macOS and Linux**:
        Open your terminal and run:
        ```bash
        ./install.sh
        ```
        This script will:
        *   Guide you through installing necessary Python packages.
        *   Set up the `start-face-framing.sh` convenience script and make it executable.
        *   Install the package in user mode, making the `start-face-framing` command available.

    The installer will also create a default `config/settings.yaml` if one doesn't exist.

## Usage

Once installed, you can start Auto Face Framing using one of the following methods:

*   **Recommended (all platforms, if PATH is configured by installer)**:
    ```bash
    start-face-framing
    ```

*   **Windows (alternative)**:
    ```batch
    ./start-face-framing.bat
    ```

*   **Linux/macOS (alternative)**:
    ```bash
    ./start-face-framing.sh
    ```
    or
    ```bash
    python3 -m autoFaceFraming.cli
    ```

### Command-Line Options

You can view available command-line options by running:
```bash
start-face-framing --help
```
This will show options for specifying a custom config file, resolution, FPS, disabling virtual camera output, and more.

### Selecting the Virtual Camera

After starting the application, "Auto Face Framing Virtual Camera" (or a similar name, depending on your OS and virtual camera driver) should appear as a camera option in your video conferencing software (e.g., Zoom, Teams, Meet). Select it to use the auto-framed video feed.

## Configuration

The application's behavior can be customized through the `config/settings.yaml` file. If this file doesn't exist in the project's root `config` directory, the application will copy the default settings from the package's `autoFaceFraming/config/settings.yaml` upon first run.

Key configurable parameters include:

*   **Camera Settings**:
    *   `camera_index`: Index of the physical camera to use (e.g., 0, 1). -1 for auto-detect.
    *   `resolution`: Desired camera resolution (e.g., `width: 1280`, `height: 720`).
    *   `frame_rate`: Desired camera frame rate (e.g., 24, 30).
*   **Face Detection**:
    *   `detector_type`: `haar` (faster, less accurate) or `dnn` (slower, more accurate).
    *   `dnn_model_path`, `dnn_proto_path`: Paths to DNN model files.
    *   `confidence_threshold`: Minimum confidence for DNN face detection.
*   **Framing Logic**:
    *   `target_face_scale`: Desired scale of the face relative to the frame height.
    *   `zoom_speed`: How quickly the camera zooms.
    *   `pan_speed`: How quickly the camera pans.
    *   `smoothing_factor`: Level of smoothing applied to camera movements.
*   **Virtual Camera**:
    *   `virtual_camera_name`: Name for the virtual camera device.
    *   `output_resolution`: Resolution for the virtual camera output.
*   **UI/Debug**:
    *   `show_debug_hud`: Display a debug overlay on the preview window.
    *   `show_preview_window`: Whether to display a local preview window.
    *   `fancy_terminal_ui`: Enable/disable enhanced terminal output.
    *   `spinner_style`: Style of the loading spinner in the terminal.

## Troubleshooting

*   **Virtual Camera Not Found**:
    *   Ensure you have a virtual camera driver installed (OBS, Unity Capture for Windows; v4l2loopback for Linux; OBS for macOS).
    *   For Linux, make sure the `v4l2loopback` module is loaded (`sudo modprobe v4l2loopback`). You might need to specify `exclusive_caps=1` when loading if some applications don't see the camera: `sudo modprobe v4l2loopback exclusive_caps=1 video_nr=10 card_label="AutoFrameCam"`. The `video_nr` should be an unused video device number.
    *   Restart your video conferencing application after starting Auto Face Framing.
*   **Low Performance/Lag**:
    *   Try a lower camera resolution or frame rate in `config/settings.yaml`.
    *   Switch to the `haar` face detector if using `dnn`.
    *   Ensure your system meets the general requirements for real-time video processing.
    *   Close other resource-intensive applications.
*   **Python Not Found (Windows)**:
    *   Ensure Python was added to your PATH during its installation. The `setup_windows.bat` script attempts to do this, but manual configuration might be needed in some cases.
*   **Permission Denied (Linux/macOS)**:
    *   Make sure `install.sh` and `start-face-framing.sh` are executable: `chmod +x install.sh start-face-framing.sh`.

## Dependencies

The project relies on several Python libraries. Key dependencies are listed in `requirements.txt` and include:

*   **opencv-python**: For all computer vision tasks.
*   **numpy**: For numerical operations, especially with image data.
*   **pyvirtualcam**: For creating the virtual camera output.
*   **PyYAML**: For loading and parsing the `settings.yaml` configuration file.
*   **colorama**: For cross-platform colored terminal text.
*   **psutil**: For system monitoring (optional, used in debug HUD).

The `install.sh` or `setup_windows.bat` scripts will help you install these.

## Contributing

Contributions are welcome! Whether it's bug fixes, feature enhancements, or documentation improvements, please feel free to:

1.  Fork the repository.
2.  Create a new branch for your feature or fix (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -am 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

Please ensure your code adheres to general Python best practices and include tests for new functionality if applicable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments

*   The **OpenCV** team and community for their invaluable computer vision library.
*   Contributors to the **pyvirtualcam** library.
*   Everyone who has provided inspiration and support for this project.

---
*Developed by Akshat Kushwaha (@a3rodev)*
*Last Updated: May 9, 2025*
