#!/bin/bash

# Auto Face Framing installer script
echo "========================================="
echo "    Auto Face Framing Installer Script   "
echo "========================================="
echo "  By Akshat Kushwaha (@a3rodev)         "
echo "  https://github.com/a3ro-dev           "
echo "========================================="
echo

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "Detected Linux OS"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "Detected macOS"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
    echo "Detected Windows OS"
else
    echo "Unsupported OS: $OSTYPE"
    echo "The install script might not work correctly. Proceeding anyway..."
fi

# Check for Python
echo "Checking for Python 3.6+..."
python_version=$(python --version 2>&1 | awk '{print $2}')
python3_version=$(python3 --version 2>&1 | awk '{print $2}')

if [[ "$python_version" =~ ^3\.[6-9] || "$python_version" =~ ^3\.[1-9][0-9] ]]; then
    python_cmd="python"
elif [[ "$python3_version" =~ ^3\.[6-9] || "$python3_version" =~ ^3\.[1-9][0-9] ]]; then
    python_cmd="python3"
else
    echo "Python 3.6 or higher is required but not found. Please install Python 3.6+."
    echo "Installation failed."
    exit 1
fi

echo "Found $python_cmd version $python_version"

# Install the package
echo "Installing Auto Face Framing package..."
$python_cmd -m pip install -e .
if [ $? -ne 0 ]; then
    echo "Failed to install the package."
    echo "Installation failed."
    exit 1
fi
echo "Package installed successfully."

# Install or check for virtual camera dependencies
if [ "$OS" = "linux" ]; then
    echo "Checking for v4l2loopback..."
    if lsmod | grep -q v4l2loopback; then
        echo "v4l2loopback module is loaded."
    else
        echo "v4l2loopback module is not loaded."
        
        # Detect Linux distribution
        if [ -f /etc/fedora-release ]; then
            echo "Detected Fedora. Installing v4l2loopback..."
            sudo dnf install -y v4l2loopback
        elif [ -f /etc/debian_version ]; then
            echo "Detected Debian/Ubuntu. Installing v4l2loopback..."
            sudo apt-get update
            sudo apt-get install -y v4l2loopback-dkms
        else
            echo "Unsupported Linux distribution. Please install v4l2loopback manually."
        fi
        
        # Try to load the module
        echo "Attempting to load v4l2loopback module..."
        sudo modprobe v4l2loopback
        if [ $? -ne 0 ]; then
            echo "Failed to load v4l2loopback module."
            echo "Please install and load it manually."
        else
            echo "v4l2loopback module loaded successfully."
        fi
    fi
elif [ "$OS" = "windows" ]; then
    echo "On Windows, you need a virtual camera driver to use the virtual camera feature."
    echo "Please install one of the following:"
    echo "1. OBS Studio (which includes OBS Virtual Camera)"
    echo "   Download from: https://obsproject.com/"
    echo "2. Unity Capture (alternative virtual camera driver)"
    echo "   Download from: https://github.com/schellingb/UnityCapture"
elif [ "$OS" = "macos" ]; then
    echo "On macOS, you need a virtual camera driver to use the virtual camera feature."
    echo "It's recommended to install OBS Studio which includes a virtual camera driver."
    echo "Download from: https://obsproject.com/"
fi

# Check for pyvirtualcam
echo "Checking for pyvirtualcam..."
if $python_cmd -c "import pyvirtualcam" &> /dev/null; then
    echo "pyvirtualcam found."
else
    echo "pyvirtualcam not found. Attempting to install..."
    $python_cmd -m pip install pyvirtualcam
    if [ $? -ne 0 ]; then
        echo "Failed to install pyvirtualcam."
        echo "Virtual camera output may not work."
    fi
fi

# Create default config directory if it doesn't exist
if [ ! -d "config" ]; then
    echo "Creating config directory..."
    mkdir -p config
fi

# Check if settings.yaml exists
if [ ! -f "config/settings.yaml" ] && [ -f "config/settings.yaml.example" ]; then
    echo "Creating default configuration..."
    cp config/settings.yaml.example config/settings.yaml
fi

# Create models directory if it doesn't exist
if [ ! -d "models" ]; then
    echo "Creating models directory..."
    mkdir -p models/face_detector
fi

# Check for face detection models
echo "Checking for face detection models..."
if [ ! -f "models/face_detector/deploy.prototxt" ] || [ ! -f "models/face_detector/res10_300x300_ssd_iter_140000.caffemodel" ]; then
    echo "Face detection DNN models not found."
    echo "You can download them manually if you want to use DNN-based detection."
    echo "Default Haar cascade will be used."
fi

echo
echo "========================================="
echo "        Installation Complete!           "
echo "========================================="
echo
echo "To run Auto Face Framing:"
echo "  start-face-framing"
echo
echo "For additional options:"
echo "  start-face-framing --help"
echo
echo "For a detailed tutorial:"
echo "  less TUTORIAL.md"
echo
echo "Visit: https://github.com/a3ro-dev/autoFaceFraming"
echo "Twitter: @a3rodev"
echo
echo "Enjoy your automatic face framing!"