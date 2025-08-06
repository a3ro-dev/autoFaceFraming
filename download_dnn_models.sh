#!/bin/bash

# Script to download DNN face detection models for Auto Face Framing

echo "Downloading DNN face detection models..."
echo "Creating models directory if it doesn't exist..."

# Create the models directory structure
mkdir -p models/face_detector

# Define the download URLs
PROTO_URL="https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
MODEL_URL="https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"

# Download the prototxt file
echo "Downloading deploy.prototxt..."
curl -L $PROTO_URL -o models/face_detector/deploy.prototxt

# Download the model file
echo "Downloading res10_300x300_ssd_iter_140000.caffemodel..."
curl -L $MODEL_URL -o models/face_detector/res10_300x300_ssd_iter_140000.caffemodel

# Check if the files were downloaded successfully
if [ -f "models/face_detector/deploy.prototxt" ] && [ -f "models/face_detector/res10_300x300_ssd_iter_140000.caffemodel" ]; then
    echo "DNN face detection models downloaded successfully!"
    echo "To use DNN-based detection, update your settings.yaml file:"
    echo "  face_detection:"
    echo "    detector_type: \"dnn\""
    echo "    confidence_threshold: 0.5"
else
    echo "Error: Failed to download one or more model files."
    exit 1
fi
