import threading

import numpy as np
import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .. import models, schemas
from ..auth import get_current_user
from ..ml.attention_tracker import extract_pose, score_pose

router = APIRouter(prefix="/attention", tags=["attention"])

_CALIBRATION_SAMPLES = 5

# Per-session calibration state, held in memory for the life of the process.
# Keyed by session_id: list of (yaw, pitch) samples while calibrating, then
# replaced with the resolved (yaw, pitch) baseline once enough are collected.
_calibration_samples: dict[int, list[tuple[float, float]]] = {}
_calibration_baseline: dict[int, tuple[float, float]] = {}
_lock = threading.Lock()


def clear_calibration(session_id: int) -> None:
    with _lock:
        _calibration_samples.pop(session_id, None)
        _calibration_baseline.pop(session_id, None)


@router.post("/analyze", response_model=schemas.FrameAnalysisOut)
async def analyze(
    frame: UploadFile = File(...),
    session_id: int | None = Form(None),
    current_user: models.User = Depends(get_current_user),
):
    contents = await frame.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    pose = extract_pose(image)

    if not pose["face_detected"] or session_id is None:
        result = score_pose(pose["yaw"], pose["pitch"], pose["eyes_closed"], pose["face_detected"])
        return {**result, **pose}

    yaw, pitch = pose["yaw"], pose["pitch"]

    with _lock:
        baseline = _calibration_baseline.get(session_id)

        if baseline is None and yaw is not None and pitch is not None and not pose["eyes_closed"]:
            samples = _calibration_samples.setdefault(session_id, [])
            samples.append((yaw, pitch))
            if len(samples) >= _CALIBRATION_SAMPLES:
                baseline = (
                    float(np.median([s[0] for s in samples])),
                    float(np.median([s[1] for s in samples])),
                )
                _calibration_baseline[session_id] = baseline
                _calibration_samples.pop(session_id, None)
            else:
                return {
                    "score": 100.0,
                    "status": "Calibrating... look at the screen",
                    "yaw": round(yaw, 1),
                    "pitch": round(pitch, 1),
                    "eyes_closed": pose["eyes_closed"],
                    "face_detected": True,
                }

    adj_yaw = yaw - baseline[0] if (baseline and yaw is not None) else yaw
    adj_pitch = pitch - baseline[1] if (baseline and pitch is not None) else pitch

    result = score_pose(adj_yaw, adj_pitch, pose["eyes_closed"], True)
    return {
        **result,
        "yaw": round(yaw, 1) if yaw is not None else None,
        "pitch": round(pitch, 1) if pitch is not None else None,
        "eyes_closed": pose["eyes_closed"],
        "face_detected": True,
    }
