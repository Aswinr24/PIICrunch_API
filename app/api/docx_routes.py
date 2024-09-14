from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from docx import Document
from docx.shared import RGBColor
from app.utils.pii_detection import detect_pii, detect_docType
from app.utils.docx_processing import redact_docx_content, process_docx_file
from docx2python import docx2python
import fitz 
import io

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
        pii_types, document_type = detect_pii(text) 
        return {"document_type": document_type, "detected_pii": pii_types}
    
    return JSONResponse(status_code=400, content={"error": "Invalid file format. Only DOCX is supported."})

@router.post("/redact")
async def redact_docx(file: UploadFile = File(...), pii_to_redact: str = Form("all")):
    contents = await file.read()

    if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(contents))
    
        full_text = "\n".join([para.text for para in doc.paragraphs])
        document_type = detect_docType(full_text)

        if pii_to_redact == "all":
            redacted_doc, redacted_texts = redact_docx_content(doc, document_type)
        else:
            pii_to_redact_list = [item.strip() for item in pii_to_redact.split(",")]
            redacted_doc, redacted_texts = process_docx_file(doc, document_type, pii_to_redact_list)

        output = io.BytesIO()
        redacted_doc.save(output)
        output.seek(0)

        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                headers={"Content-Disposition": "attachment; filename=processed_docx.docx"})
    
    return JSONResponse(status_code=400, content={"error": "Invalid DOCX format."})