"""
core/embedder.py
-----------------
Face embeddings using facenet-pytorch — PyTorch-based Facenet.

No TensorFlow dependency — works on Python 3.11+ and Streamlit Cloud.

FIRST RUN:
Run this in your terminal ONCE before starting the app:
    pip install facenet-pytorch torch torchvision --index-url https://download.pytorch.org/whl/cpu

The model weights (~90MB) download automatically on first use.
"""

import numpy as np
import cv2

_MODEL = None


def _get_model():
    """
    Loads InceptionResnetV1 pretrained on VGGFace2.
    Cached at module level — loads once, reused on every call.
    """
    global _MODEL
    if _MODEL is None:
        try:
            import torch
            from facenet_pytorch import InceptionResnetV1
            _MODEL = InceptionResnetV1(pretrained="vggface2").eval()
        except ImportError:
            raise ImportError(
                "facenet-pytorch is not installed.\n"
                "Run: pip install facenet-pytorch torch torchvision "
                "--index-url https://download.pytorch.org/whl/cpu"
            )
    return _MODEL


def warm_up_model():
    """
    Called once at startup. Forces model weights to load into memory
    so the first real upload doesn't carry the cold-start delay.
    """
    try:
        import torch
        model = _get_model()
        dummy = torch.zeros(1, 3, 160, 160)
        with torch.no_grad():
            model(dummy)
        print("TraceKE: Facenet model loaded and ready.")
    except Exception as e:
        print(f"TraceKE: warm-up warning (non-fatal): {e}")


def _preprocess(face_bgr: np.ndarray):
    """
    Prepares a BGR face crop for Facenet.
    BGR → RGB → resize 160×160 → normalise [-1,1] → tensor (1,3,160,160)
    """
    import torch
    rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (160, 160))
    tensor = torch.from_numpy(resized).float()
    tensor = (tensor / 255.0 - 0.5) / 0.5
    tensor = tensor.permute(2, 0, 1).unsqueeze(0)
    return tensor


def get_embedding(face_image: np.ndarray) -> list:
    """
    Converts a cropped face (BGR NumPy array) into a 512-number vector.
    Raises a clear error if it fails — no silent swallowing.
    """
    import torch

    if face_image is None or face_image.size == 0:
        raise ValueError("Empty face image passed to get_embedding.")

    # ensure image is large enough to process
    h, w = face_image.shape[:2]
    if h < 20 or w < 20:
        raise ValueError(f"Face crop too small ({w}×{h}px) for embedding.")

    model = _get_model()
    tensor = _preprocess(face_image)

    with torch.no_grad():
        embedding = model(tensor)

    emb = embedding.squeeze().numpy()

    # L2-normalise for cosine similarity
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm

    return emb.tolist()


def get_average_embedding(face_images: list) -> list:
    """
    Averages embeddings from multiple photos of the same person.
    Now shows the real error if all photos fail instead of hiding it.
    """
    if len(face_images) == 1:
        return get_embedding(face_images[0])

    embeddings = []
    errors = []

    for i, face in enumerate(face_images):
        try:
            embeddings.append(get_embedding(face))
        except Exception as e:
            errors.append(f"Photo {i+1}: {e}")

    if not embeddings:
        error_detail = " | ".join(errors)
        raise ValueError(
            f"No valid embeddings generated from {len(face_images)} photo(s). "
            f"Errors: {error_detail}\n\n"
            f"Make sure facenet-pytorch is installed: "
            f"pip install facenet-pytorch torch torchvision "
            f"--index-url https://download.pytorch.org/whl/cpu"
        )

    avg = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg)
    if norm > 0:
        avg = avg / norm

    return avg.tolist()
