from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
# import fitz  
from app.utils.pii_detection import detect_pii, detect_docType
from app.utils.image_processing import redact, redact_specific_pii
from pdf2image import convert_from_bytes
from PIL import Image, ImageEnhance
import numpy as np
import easyocr
import io
import cv2

router = APIRouter()
reader = easyocr.Reader(['en'])

@router.post("/detect")
async def detect_pii_pdf(file: UploadFile = File(...)):
    contents = await file.read()

    if file.content_type == "application/pdf":
        images = convert_from_bytes(contents)
        text = ""
        # pdf_document = fitz.open(stream=contents, filetype="pdf")
        # for page_num in range(len(pdf_document)):
        #     page = pdf_document.load_page(page_num)
        #     text += page.get_text()
        # pdf_document.close()
        for image in images:
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')  
            image_bytes.seek(0)
            ocr_results = reader.readtext(image_bytes.read())  
            page_text = " ".join([result[1] for result in ocr_results])
            text += page_text + "\n"
        pii_types, document_type = detect_pii(text) 
        return {"document_type": document_type, "detected_pii": pii_types}
    
    return JSONResponse(status_code=400, content={"error": "Invalid file format. Only PDFs are supported."})

@router.post("/redact")
async def redact_pdf(file: UploadFile = File(...), pii_to_redact: str = Form("all")):
    contents = await file.read()
    pii_to_redact_list = pii_to_redact.split(",")
    if file.content_type == "application/pdf":
        images = convert_from_bytes(contents)
        redacted_images = []
        for image in images:
            np_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')  
            image_bytes.seek(0)
            results = reader.readtext(image_bytes.read())  
            page_text = " ".join([result[1] for result in results])
            document_type=detect_docType(page_text)
            if pii_to_redact == 'all':
                processed_image = redact(np_image, results, document_type)
            else:
                processed_image = redact_specific_pii(np_image, results, document_type, pii_to_redact_list)
            pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
            upscale_factor = 2
            pil_image = pil_image.resize((pil_image.width * upscale_factor, pil_image.height * upscale_factor), Image.LANCZOS)
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(2.0)
            redacted_images.append(pil_image)

        pdf_buffer = io.BytesIO()

        if redacted_images:
            redacted_images[0].save(pdf_buffer,format='PDF',save_all=True, append_images=redacted_images[1:])
        pdf_buffer.seek(0)
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=redacted.pdf"})

    return JSONResponse(status_code=400, content={"error": "PDF redaction is not yet implemented"})
