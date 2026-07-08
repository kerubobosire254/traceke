"""
core/detector.py
-----------------
Face detection with two-tier approach:
1. YuNet (OpenCV DNN) — preferred, better dark skin tone detection
2. Haar Cascade — automatic fallback if YuNet model unavailable

KEY FIX: Streamlit uploaded file objects must be seeked to position 0
before reading. Inside st.form(), the file pointer can be consumed.
We always call image_input.seek(0) before opening with PIL.
"""

import cv2
import numpy as np
from PIL import Image
import os
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "assets", "face_detection_yunet.onnx")

_yunet = None
_haar = None


def _download_yunet():
    """Try to download YuNet model. Returns True if successful."""
    urls = [
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    ]
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    for url in urls:
        try:
            import urllib.request
            urllib.request.urlretrieve(url, MODEL_PATH)
            if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10000:
                print("TraceKE: YuNet model downloaded.")
                return True
        except Exception:
            continue
    return False


def _get_detector(image_w: int, image_h: int):
    """Returns (type, detector) — YuNet if available, Haar otherwise."""
    global _yunet, _haar

    # try YuNet
    if not (os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10000):
        _download_yunet()

    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10000:
        try:
            _yunet = cv2.FaceDetectorYN_create(
                model=MODEL_PATH,
                config="",
                input_size=(image_w, image_h),
                score_threshold=0.4,
                nms_threshold=0.3,
                top_k=10
            )
            return "yunet", _yunet
        except Exception as e:
            print(f"TraceKE: YuNet init failed ({e}), using Haar.")

    # Haar Cascade fallback
    if _haar is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _haar = cv2.CascadeClassifier(cascade_path)
    return "haar", _haar


def load_image(image_input) -> np.ndarray:
    """
    Loads an image from a file path OR a Streamlit uploaded file object.

    CRITICAL: For Streamlit file objects, we MUST seek to position 0 first.
    Inside st.form(), Streamlit may have already read the file buffer once
    during the widget render cycle. Without seek(0), PIL gets an empty
    stream and produces a blank image — which means zero faces detected,
    which means every photo appears to fail detection.
    """
    if isinstance(image_input, str):
        # file path — straightforward imread
        image = cv2.imread(image_input)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {image_input}")
        return image

    # Streamlit UploadedFile or any file-like object
    try:
        # seek to start in case the buffer was already read
        image_input.seek(0)
    except Exception:
        pass

    # read bytes into memory buffer so PIL can open it reliably
    file_bytes = image_input.read()
    if not file_bytes:
        raise ValueError("Uploaded file is empty or could not be read.")

    # open from bytes buffer — works regardless of file object state
    pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image = np.array(pil_image)
    # PIL gives RGB, OpenCV needs BGR
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image


def detect_faces(image_input):
    """
    Detects all faces. Returns (image_array, list_of_bounding_boxes).
    Bounding boxes are (x, y, w, h). Empty list means no faces found.
    """
    image = load_image(image_input)
    h, w = image.shape[:2]

    if h == 0 or w == 0:
        return image, []

    detector_type, detector = _get_detector(w, h)
    faces = []

    if detector_type == "yunet":
        detector.setInputSize((w, h))
        _, detections = detector.detect(image)
        if detections is not None:
            for det in detections:
                x = max(0, int(det[0]))
                y = max(0, int(det[1]))
                fw = min(int(det[2]), w - x)
                fh = min(int(det[3]), h - y)
                if fw > 10 and fh > 10:
                    faces.append((x, y, fw, fh))
    else:
        # Haar with CLAHE preprocessing for better dark skin detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        detections = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,   # lowered from 5 — more permissive
            minSize=(20, 20)  # lowered from 30 — catches smaller faces
        )
        if len(detections) > 0:
            faces = [tuple(d) for d in detections]

    return image, faces


def assess_photo_quality(image: np.ndarray) -> dict:
    """
    Labels photo quality — NEVER blocks. Returns context for reviewer only.
    CLAHE normalisation applied before measurement — skin-tone neutral.
    """
    if image is None or image.size == 0:
        return {"confidence_level": "low", "notes": ["could not assess image"], "blur_score": 0, "brightness": 0, "resolution": "0x0"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    normalized = clahe.apply(gray)

    blur_score = cv2.Laplacian(normalized, cv2.CV_64F).var()
    brightness = np.mean(gray)
    h, w = image.shape[:2]

    notes = []
    if blur_score < 30:
        notes.append("lower sharpness detected")
    if brightness < 40:
        notes.append("low light conditions")
    elif brightness > 230:
        notes.append("overexposed")
    if w < 150 or h < 150:
        notes.append("low resolution")

    if not notes:
        level = "high"
    elif len(notes) == 1:
        level = "moderate"
    else:
        level = "low"

    return {
        "confidence_level": level,
        "notes": notes,
        "blur_score": round(blur_score, 1),
        "brightness": round(brightness, 1),
        "resolution": f"{w}x{h}"
    }


def crop_face(image: np.ndarray, face: tuple, padding: int = 30) -> np.ndarray:
    """Crops a face from the image with padding for better embedding context."""
    x, y, w, h = face
    img_h, img_w = image.shape[:2]
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(img_w, x + w + padding)
    y2 = min(img_h, y + h + padding)
    return image[y1:y2, x1:x2]


def draw_boxes(image: np.ndarray, faces: list, selected_idx: int = None) -> np.ndarray:
    """Draws numbered bounding boxes on detected faces."""
    annotated = image.copy()
    for i, (x, y, w, h) in enumerate(faces):
        selected = (selected_idx is not None and i == selected_idx)
        color = (0, 180, 160) if selected else (150, 150, 150)
        thickness = 3 if selected else 1
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)
        cv2.putText(annotated, str(i + 1), (x + 6, y + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2)
    return annotated
