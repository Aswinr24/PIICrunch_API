from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List
from app.utils.pii_detection import detect_pii, detect_docType
from app.utils.image_processing import redact, redact_specific_pii
import cv2
import io
import numpy as np
import easyocr

router = APIRouter()
reader = easyocr.Reader(['en'], gpu=False)

async def validate_and_read_image(file: UploadFile):
    """Validate and read image content."""
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Only JPG and PNG are supported.")
    return await file.read()

@router.post("/detect")
async def detect_pii_in_image(file: UploadFile = File(...)):
    contents = await validate_and_read_image(file)
    
    # Extract text from the image using OCR
    results = reader.readtext(contents)
    text = " ".join([result[1] for result in results])
    
    # Detect PII types in extracted text
    pii_types, document_type = detect_pii(text)
    return {"document_type": document_type, "detected_pii": pii_types}

@router.post("/redact")
async def redact_pii_in_image(file: UploadFile = File(...), pii_to_redact: str = Form("all")):
    contents = await validate_and_read_image(file)
    pii_to_redact_list = [item.strip() for item in pii_to_redact.split(",")]
    
    # Decode image and validate
    np_array = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Unable to decode the image. Please check the file format.")
    
    # Extract text from the image using OCR
    results = reader.readtext(image)
    text = " ".join([result[1] for result in results])
    
    # Detect document type based on content
    document_type = detect_docType(text)
    
    # Redact PII based on specified categories
    if pii_to_redact == 'all':
        processed_image = redact(image, results, document_type)
    else:
        processed_image = redact_specific_pii(image, results, document_type, pii_to_redact_list)
    
    # Encode processed image for streaming response
    success, img_encoded = cv2.imencode('.png', processed_image)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode the image.")
    
    # Return redacted image as response
    output = io.BytesIO(img_encoded.tobytes())
    output.seek(0)
    return StreamingResponse(output, media_type="image/png", headers={"Content-Disposition": "attachment; filename=redacted_image.png"})
