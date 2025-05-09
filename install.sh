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
    
    # On Windows, try to add Python to PATH if needed
    if [ "$OS" = "windows" ]; then
        echo "Checking if Python is in PATH..."
        python_in_path=false
        if command -v python &>/dev/null; then
            python_in_path=true
            echo "Python is already in PATH."
        elif command -v py &>/dev/null; then
            python_in_path=true
            echo "Python launcher (py) is in PATH."
        else
            echo "Python not found in PATH."
        fi
        
        if [ "$python_in_path" = false ]; then
            echo "Attempting to add Python to PATH..."
            
            # Try to find Python installation directory
            for py_dir in "/c/Python"* "/c/Program Files/Python"* "/c/Users/$USER/AppData/Local/Programs/Python"*; do
                if [ -d "$py_dir" ]; then
                    echo "Found Python at: $py_dir"
                    echo "Adding Python to PATH for this session..."
                    export PATH="$py_dir:$py_dir/Scripts:$PATH"
                    
                    # Create a PowerShell script to add Python to PATH permanently
                    echo "Creating a script to permanently add Python to PATH..."
                    cat > add_python_to_path.ps1 << EOF
\$pythonDir = "$py_dir"
\$pythonScriptsDir = "$py_dir\\Scripts"

# Get the current PATH from the registry
\$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")

# Check if Python paths are already in PATH
\$pathsToAdd = @()
if (\$currentPath -notlike "*\$pythonDir*") {
    \$pathsToAdd += \$pythonDir
}
if (\$currentPath -notlike "*\$pythonScriptsDir*") {
    \$pathsToAdd += \$pythonScriptsDir
}

if (\$pathsToAdd.Count -gt 0) {
    # Add Python paths to PATH
    \$newPath = \$currentPath
    foreach (\$path in \$pathsToAdd) {
        if (\$newPath) {
            \$newPath = "\$newPath;\$path"
        } else {
            \$newPath = "\$path"
        }
    }
    
    # Update PATH in the registry
    [Environment]::SetEnvironmentVariable("PATH", \$newPath, "User")
    Write-Host "Python has been added to your PATH. You may need to restart your terminal or computer for changes to take effect."
} else {
    Write-Host "Python is already in your PATH."
}
EOF
                    
                    echo "To permanently add Python to PATH, please run the following command as Administrator in PowerShell:"
                    echo "    powershell -ExecutionPolicy Bypass -File add_python_to_path.ps1"
                    break
                fi
            done
            
            if [ ! -f "add_python_to_path.ps1" ]; then
                echo "Could not locate Python installation. Please add Python to PATH manually."
                echo "Typically, you can do this by:"
                echo "1. Right-click on 'This PC' and select 'Properties'"
                echo "2. Click on 'Advanced system settings'"
                echo "3. Click on 'Environment Variables'"
                echo "4. Under 'User variables', select 'Path' and click 'Edit'"
                echo "5. Click 'New' and add the path to your Python installation and the Scripts folder"
            fi
        fi
    fi
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
$python_cmd -m pip install --user -e .
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
echo "╭───────────────────────────────────────────────────────────────╮"
echo "│                                                               │"
echo "│   █ █▄░█ █▀ ▀█▀ ▄▀█ █░░ █░░ ▄▀█ ▀█▀ █ █▀█ █▄░█               │"
echo "│   █ █░▀█ ▄█ ░█░ █▀█ █▄▄ █▄▄ █▀█ ░█░ █ █▄█ █░▀█               │"
echo "│                                                               │"
echo "│                █▀▀ █▀█ █▀▄▀█ █▀█ █░░ █▀▀ ▀█▀ █▀▀ █           │"
echo "│                █▄▄ █▄█ █░▀░█ █▀▀ █▄▄ ██▄ ░█░ ██▄ ▄           │"
echo "│                                                               │"
echo "╰───────────────────────────────────────────────────────────────╯"
echo
echo "To run Auto Face Framing:"
if [ "$OS" = "windows" ]; then
    echo "  Method 1: Use the batch file (recommended for Windows):"
    echo "     ./start-face-framing.bat"
    echo ""
    echo "  Method 2: Run the Python module directly:"
    echo "     python -m autoFaceFraming.cli"
    echo ""
    echo "  Method 3: If you added Python Scripts to your PATH:"
    echo "     start-face-framing"
else
    echo "  Method 1: Using the shell script:"
    echo "     ./start-face-framing.sh"
    echo ""
    echo "  Method 2: Using the installed entry point:"
    echo "     start-face-framing"
    echo ""
    echo "  Method 3: Running the Python module directly:"
    echo "     python -m autoFaceFraming.cli"
fi
echo
echo "For additional options, add --help to any of the above commands."
echo
echo "For a detailed tutorial:"
if [ "$OS" = "windows" ]; then
    echo "  notepad TUTORIAL.md   or   type TUTORIAL.md"
else
    echo "  less TUTORIAL.md"
fi
echo
echo "Visit: https://github.com/a3ro-dev/autoFaceFraming"
echo "Twitter: @a3rodev"
echo
echo "Enjoy your automatic face framing!"