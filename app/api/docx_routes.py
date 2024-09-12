from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from docx import Document
from docx.shared import RGBColor
import io
from app.utils.pii_detection import detect_pii
from docx2python import docx2python
import fitz  # PyMuPDF

router = APIRouter()

@router.post("/detect")
async def detect_pii_docx(file: UploadFile = File(...)):
    contents = await file.read()

    if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = fitz.open(stream=contents, filetype="docx")
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        print(text)
        pii_types, document_type = detect_pii(text) 
        return {"document_type": document_type, "detected_pii": pii_types}
    
    return JSONResponse(status_code=400, content={"error": "Invalid file format. Only DOCX is supported."})

@router.post("/redact")
async def redact_docx(file: UploadFile = File(...), action: str = Form(...)):
    contents = await file.read()

    if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(contents))
        
        for para in doc.paragraphs:
            for run in para.runs:
                if "Aadhaar" in run.text or "Phone" in run.text:  # Example PII matching logic
                    if action == "mask":
                        run.text = "XXXX-XXXX-XXXX"
                    elif action == "blur":
                        run.font.color.rgb = RGBColor(192, 192, 192)  # Blur (fading text)

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return FileResponse(output, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="processed_docx.docx")

    return JSONResponse(status_code=400, content={"error": "Invalid DOCX format."})
