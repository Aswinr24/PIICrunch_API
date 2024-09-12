from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
# import fitz  
from app.utils.pii_detection import detect_pii
from pdf2image import convert_from_bytes
import easyocr
import io

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
async def redact_pdf(file: UploadFile = File(...), action: str = Form(...)):
    # Placeholder for PDF redaction logic
    return JSONResponse(status_code=400, content={"error": "PDF redaction is not yet implemented"})
