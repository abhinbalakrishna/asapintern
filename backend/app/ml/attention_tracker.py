"""
Webcam-frame attention scoring.

Pipeline: MediaPipe FaceMesh (pretrained) locates facial landmarks -> a
solvePnP head-pose estimate gives yaw/pitch -> eye-aspect-ratio (EAR) on
the eye landmarks detects closed eyes.

The generic 3D face model and the focal-length approximation used here
only give a rough yaw/pitch estimate: the absolute numbers carry a
per-person, per-camera bias (different face shape, camera placement,
etc.), so "0 degrees" from solvePnP does not reliably mean "looking at
the screen". Callers should calibrate by averaging a few frames of the
user looking at the screen and comparing later readings against that
baseline instead of against zero -- see routers/attention.py.
"""

import threading

import cv2
import numpy as np
import mediapipe as mp

_mp_face_mesh = mp.solutions.face_mesh

# One shared FaceMesh instance; MediaPipe graphs aren't thread-safe so all
# calls are serialized behind this lock (fine for a single-user demo).
_face_mesh = _mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
_lock = threading.Lock()

# Canonical 3D face model points (mm), paired with FaceMesh landmark indices below.
_MODEL_POINTS = np.array(
    [
        (0.0, 0.0, 0.0),  # Nose tip
        (0.0, -330.0, -65.0),  # Chin
        (-225.0, 170.0, -135.0),  # Left eye, left corner
        (225.0, 170.0, -135.0),  # Right eye, right corner
        (-150.0, -150.0, -125.0),  # Left mouth corner
        (150.0, -150.0, -125.0),  # Right mouth corner
    ],
    dtype=np.float64,
)

_LANDMARK_IDX = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_left_corner": 33,
    "right_eye_right_corner": 263,
    "left_mouth_corner": 61,
    "right_mouth_corner": 291,
}

_LEFT_EYE = [33, 160, 158, 133, 153, 144]
_RIGHT_EYE = [362, 385, 387, 263, 373, 380]

_EAR_THRESHOLD = 0.21
_YAW_OK_DEG = 15.0
_PITCH_OK_DEG = 13.0


def _eye_aspect_ratio(landmarks, idx, w, h):
    pts = np.array([(landmarks[i].x * w, landmarks[i].y * h) for i in idx])
    vertical_1 = np.linalg.norm(pts[1] - pts[5])
    vertical_2 = np.linalg.norm(pts[2] - pts[4])
    horizontal = np.linalg.norm(pts[0] - pts[3])
    if horizontal == 0:
        return 0.4
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def _rotation_matrix_to_euler(rmat):
    sy = np.sqrt(rmat[0, 0] ** 2 + rmat[1, 0] ** 2)
    singular = sy < 1e-6
    if not singular:
        pitch = np.arctan2(rmat[2, 1], rmat[2, 2])
        yaw = np.arctan2(-rmat[2, 0], sy)
        roll = np.arctan2(rmat[1, 0], rmat[0, 0])
    else:
        pitch = np.arctan2(-rmat[1, 2], rmat[1, 1])
        yaw = np.arctan2(-rmat[2, 0], sy)
        roll = 0
    return np.degrees(pitch), np.degrees(yaw), np.degrees(roll)


def extract_pose(image_bgr: np.ndarray) -> dict:
    """Runs FaceMesh + solvePnP and returns raw, uncalibrated pose features."""
    h, w = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    with _lock:
        result = _face_mesh.process(image_rgb)

    if not result.multi_face_landmarks:
        return {"face_detected": False, "yaw": None, "pitch": None, "eyes_closed": False}

    landmarks = result.multi_face_landmarks[0].landmark

    image_points = np.array(
        [
            (landmarks[_LANDMARK_IDX["nose_tip"]].x * w, landmarks[_LANDMARK_IDX["nose_tip"]].y * h),
            (landmarks[_LANDMARK_IDX["chin"]].x * w, landmarks[_LANDMARK_IDX["chin"]].y * h),
            (landmarks[_LANDMARK_IDX["left_eye_left_corner"]].x * w, landmarks[_LANDMARK_IDX["left_eye_left_corner"]].y * h),
            (landmarks[_LANDMARK_IDX["right_eye_right_corner"]].x * w, landmarks[_LANDMARK_IDX["right_eye_right_corner"]].y * h),
            (landmarks[_LANDMARK_IDX["left_mouth_corner"]].x * w, landmarks[_LANDMARK_IDX["left_mouth_corner"]].y * h),
            (landmarks[_LANDMARK_IDX["right_mouth_corner"]].x * w, landmarks[_LANDMARK_IDX["right_mouth_corner"]].y * h),
        ],
        dtype=np.float64,
    )

    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
        dtype=np.float64,
    )
    dist_coeffs = np.zeros((4, 1))

    success, rotation_vec, _ = cv2.solvePnP(
        _MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )

    yaw = pitch = None
    if success:
        rmat, _ = cv2.Rodrigues(rotation_vec)
        pitch, yaw, _roll = _rotation_matrix_to_euler(rmat)

    left_ear = _eye_aspect_ratio(landmarks, _LEFT_EYE, w, h)
    right_ear = _eye_aspect_ratio(landmarks, _RIGHT_EYE, w, h)
    avg_ear = (left_ear + right_ear) / 2.0
    eyes_closed = avg_ear < _EAR_THRESHOLD

    return {
        "face_detected": True,
        "yaw": float(yaw) if yaw is not None else None,
        "pitch": float(pitch) if pitch is not None else None,
        "eyes_closed": bool(eyes_closed),
    }


def score_pose(yaw: float | None, pitch: float | None, eyes_closed: bool, face_detected: bool) -> dict:
    """Turns (baseline-adjusted) yaw/pitch into a 0-100 score + status."""
    if not face_detected:
        return {"score": 0.0, "status": "No face detected"}

    if eyes_closed:
        return {"score": 15.0, "status": "Eyes closed / drowsy"}

    if yaw is None or pitch is None:
        return {"score": 50.0, "status": "Face detected"}

    yaw_penalty = max(0.0, abs(yaw) - _YAW_OK_DEG) * 2.2
    pitch_penalty = max(0.0, abs(pitch) - _PITCH_OK_DEG) * 2.2
    score = max(0.0, 100.0 - yaw_penalty - pitch_penalty)
    status = "Focused" if score >= 70 else "Looking away"
    return {"score": round(float(score), 1), "status": status}
