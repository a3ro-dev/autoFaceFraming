# Auto Face Framing
## Overview
Auto Face Framing is a Python application designed to provide a virtual camera output that detects and tracks the user's face in real-time. The application utilizes OpenCV for face detection and tracking, ensuring that the user's face remains centered in the frame while providing a smooth video output. This is particularly useful for video conferencing applications, allowing users to maintain a professional appearance during calls.

## Features
- Real-time face detection using OpenCV.
- Smooth tracking of the user's face, with automatic zoom adjustments based on distance.
- Stabilized video output to ensure a clear and crisp viewing experience.
- Configurable settings for camera resolution and frame rate.
- Compatible with various video conferencing applications as a virtual camera.

## Project Structure
```
my-virtual-camera
├── src
│   ├── main.py               # Entry point for the application
│   ├── face_detector.py      # Face detection functionality
│   ├── tracker.py            # Face tracking logic
│   ├── camera_stream.py      # Camera input and output management
│   └── utils
│       └── video_utils.py    # Utility functions for video processing
├── config
│   └── settings.yaml         # Configuration settings for the application
├── requirements.txt          # List of dependencies
├── setup.py                  # Packaging information
└── README.md                 # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/a3ro-dev/autofaceframing
   cd autofaceframing
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the settings in `config/settings.yaml` as needed.

### Windows

Option 1 (Recommended): Run the automated installer with admin rights
```
setup_windows.bat
```
This will:
- Add Python to your PATH (if needed)
- Install required dependencies
- Create necessary configuration files
- Set up the virtual camera

Option 2: Manual installation
```
install.sh
```

### macOS and Linux
```
./install.sh
```

## Usage
To run the application, execute the following command:
```
python src/main.py
```

Ensure that your camera is connected and accessible. The application will start the camera stream, detect your face, and provide a virtual camera output.

## Configuration
The application settings can be adjusted in the `config/settings.yaml` file. You can modify parameters such as:
- Camera resolution
- Frame rate
- Other relevant settings

## Dependencies
The project requires the following Python libraries:
- OpenCV
- NumPy
- Additional libraries as specified in `requirements.txt`

## Contribution
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments
- OpenCV for computer vision capabilities.
- The community for support and inspiration in developing this application.
