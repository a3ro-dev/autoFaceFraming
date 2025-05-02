# Face Detector Models

This directory is used to store face detection models used by the autoFaceFraming package.

## DNN Models

For DNN-based face detection, you need the following files:

1. `deploy.prototxt` - The network architecture file
2. `res10_300x300_ssd_iter_140000.caffemodel` - The pre-trained model weights

You can download these files from the OpenCV repository or other sources.

## Default Behavior

If the DNN model files are not found, the system will automatically fall back to using Haar cascade classifiers, which are included with OpenCV. 