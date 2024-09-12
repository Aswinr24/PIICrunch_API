from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from typing import List
from app.utils.pii_detection import detect_pii
from app.utils.image_processing import preprocess_image, get_pii_regions, mask_or_blur_image
from PIL import Image
import io
# import pytesseract
import easyocr

router = APIRouter()
reader = easyocr.Reader(['en'])

@router.post("/detect")
async def detect_pii_image(file: UploadFile = File(...)):
    contents = await file.read()

    if file.content_type in ["image/jpeg", "image/png"]:
        # image = Image.open(io.BytesIO(contents))
        # text = pytesseract.image_to_string(image)
        results = reader.readtext(contents)
        text = " ".join([result[1] for result in results])
        pii_types, document_type = detect_pii(text) 
        return {"document_type": document_type, "detected_pii": pii_types}
    
    return JSONResponse(status_code=400, content={"error": "Invalid image format. Only JPG and PNG are supported."})

@router.post("/redact")
async def redact_image(file: UploadFile = File(...), action: str = Form(...)):
    contents = await file.read()

    if file.content_type in ["image/jpeg", "image/png"]:
        image = Image.open(io.BytesIO(contents))
        preprocessed_image = preprocess_image(image)
        pii_regions = get_pii_regions(image)
        processed_image = mask_or_blur_image(image, pii_regions, action)
        output = io.BytesIO()
        processed_image.save(output, format="PNG")
        output.seek(0)
        return StreamingResponse(output, media_type="image/png", headers={"Content-Disposition": "attachment; filename=processed_image.png"})
    
    return JSONResponse(status_code=400, content={"error": "Invalid image format. Only JPG and PNG are supported."})
 