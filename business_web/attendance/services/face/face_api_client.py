"""Local Face Recognition Service using InsightFace without external APIs.

Provides simple functions to register and recognize faces directly
by querying the local SQLite database.
"""
import logging
import cv2
import numpy as np
from typing import Optional, Dict

logger = logging.getLogger('face.engine')

class FaceApiError(Exception):
    def __init__(self, code: str, message: str = ''):
        super().__init__(message or code)
        self.code = code
        self.message = message

# Global face app to prevent reloading model on every request
_face_app = None

def get_face_app():
    global _face_app
    if _face_app is None:
        try:
            from insightface.app import FaceAnalysis
            _face_app = FaceAnalysis(name='buffalo_l')
            _face_app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace model 'buffalo_l' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load InsightFace: {e}")
            raise FaceApiError("unknown", f"AI Initialization Error: {e}")
    return _face_app


def _extract_embedding(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise FaceApiError('bad_response', 'Invalid image data')
        
    app = get_face_app()
    faces = app.get(img)
    if not faces:
        raise FaceApiError('no_face', 'No face detected in image')
        
    # Take the largest face
    best_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    emb = best_face.embedding
    
    # L2 Normalize
    emb = emb / np.linalg.norm(emb)
    return emb


def health_check() -> bool:
    """Warm up the model and check if it's working."""
    try:
        get_face_app()
        return True
    except Exception:
        return False


def register_face_remote(employee_id: str, image_bytes: bytes,
                         filename: str = 'face.jpg',
                         slot_id: Optional[int] = None) -> dict:
    """Extracts embedding and returns it. 
    The calling service (face_service.py) handles saving to DB.
    """
    emb = _extract_embedding(image_bytes)
    return {
        "status": "success",
        "embedding": emb.tolist(),
        "message": "Face processed successfully."
    }


def recognize_face_remote(image_bytes: bytes,
                          filename: str = 'probe.jpg') -> dict:
    """Compares the uploaded face against all embeddings in SQLite."""
    try:
        target_emb = _extract_embedding(image_bytes)
    except FaceApiError as e:
        if e.code == 'no_face':
            return {"status": "fail", "message": "No face detected in image"}
        raise
        
    from attendance.models import EmployeeFace
    
    # Fetch all registered faces
    faces = EmployeeFace.objects.exclude(embedding__isnull=True)
    
    best_user_id = None
    best_score = -1.0 # Cosine similarity score [-1, 1]
    
    # Threshold for ArcFace buffalo_l is usually around 0.40 - 0.50 (cosine similarity)
    # Note: InsightFace embeddings when normalized, dot product = cosine similarity.
    # Higher dot product = more similar.
    SIMILARITY_THRESHOLD = 0.45 
    
    for f in faces:
        if not f.embedding:
            continue
        try:
            db_emb = np.array(f.embedding, dtype=np.float32)
            similarity = np.dot(target_emb, db_emb)
            if similarity > best_score:
                best_score = similarity
                best_user_id = f.user_id
        except Exception as e:
            logger.warning(f"Failed to compare with user {f.user_id}: {e}")
            
    if best_user_id and best_score >= SIMILARITY_THRESHOLD:
        confidence = round(float(best_score) * 100, 2)
        return {
            "status": "success",
            "employee_id": str(best_user_id),
            "confidence": f"{confidence}%",
            "match_slot": 1
        }
    else:
        return {"status": "fail", "message": "Unknown person or no match found."}
