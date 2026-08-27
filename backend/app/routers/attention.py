import numpy as np
import cv2
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from .. import models, schemas
from ..auth import get_current_user
from ..ml.attention_tracker import analyze_frame

router = APIRouter(prefix="/attention", tags=["attention"])


@router.post("/analyze", response_model=schemas.FrameAnalysisOut)
async def analyze(
    frame: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    contents = await frame.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    result = analyze_frame(image)
    return result
