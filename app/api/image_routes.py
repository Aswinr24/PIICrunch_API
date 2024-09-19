from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from typing import List
from app.utils.pii_detection import detect_pii, detect_docType
from app.utils.image_processing import redact, redact_specific_pii
import cv2
import io
# import pytesseract
import numpy as np
import easyocr

router = APIRouter()
reader = easyocr.Reader(['en'], gpu=False)

@router.post("/detect")
async def detect_pii_image(file: UploadFile = File(...)):
    contents = await file.read()

    if file.content_type in ["image/jpeg", "image/png"]:
        # image = Image.open(io.BytesIO(contents))
        # text = pytesseract.image_to_string(image)
        results = reader.readtext(contents)
        for text in results:
            print(text)
        text = " ".join([result[1] for result in results])
        pii_types, document_type = detect_pii(text) 
        return {"document_type": document_type, "detected_pii": pii_types}
    
    return JSONResponse(status_code=400, content={"error": "Invalid image format. Only JPG and PNG are supported."})

@router.post("/redact")
async def redact_image(file: UploadFile = File(...), pii_to_redact: str = Form("all")):
    contents = await file.read() 
    pii_to_redact_list = pii_to_redact.split(",")
    if file.content_type in ["image/jpeg", "image/png"]:
        np_array = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return {"error": "Unable to decode the image. Please check the file format."}
        results = reader.readtext(image)
        text = " ".join([result[1] for result in results])
        document_type = detect_docType(text)
        
        if pii_to_redact == 'all':
            processed_image = redact(image, results, document_type)
        else:
            processed_image = redact_specific_pii(image, results, document_type, pii_to_redact_list)
        
        success, img_encoded = cv2.imencode('.png', processed_image)
        if not success:
            return {"error": "Failed to encode the image."}
        
        output = io.BytesIO(img_encoded.tobytes())
        output.seek(0)
        return StreamingResponse(output, media_type="image/png", headers={"Content-Disposition": "attachment; filename=processed_image.png"})

    return JSONResponse(status_code=400, content={"error": "Invalid image format. Only JPG and PNG are supported."})
