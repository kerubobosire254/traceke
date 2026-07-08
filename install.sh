#!/bin/bash
echo "Installing TraceKE dependencies..."
pip install facenet-pytorch torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install streamlit opencv-python-headless chromadb pillow numpy pandas
echo "Done. Run: streamlit run main.py"
