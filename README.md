# PIICrunch API

PIICrunch API provides endpoints for handling PII (Personally Identifiable Information) redaction from documents such as images, PDFs, and DOCX files. This API allows you to detect and redact PII from these documents.

## Endpoints

### Image Endpoints

#### POST /image/detect

Detects PII from an image.

- **Request Parameters**: Multipart/form-data with an image file.
- **Response**: JSON object with detected PII tags.

#### POST /image/redact

Redacts PII from an image.

- **Request Body**: Multipart/form-data with an image file and a form field for `pii_to_redact` (comma-separated list of PII types to redact).
- **Response**: Redacted image.

### PDF Endpoints

#### POST /pdf/detect

Detects PII from a PDF.

- **Request Parameters**: Multipart/form-data with the pdf file.
- **Response**: JSON object with detected PII tags.

#### POST /pdf/redact

Redacts PII from a PDF.

- **Request Body**: Multipart/form-data with a pdf file and a form field for `pii_to_redact` (comma-separated list of PII types to redact).
- **Response**: Redacted image.

### DOCX Endpoints

#### POST /docx/detect

Detects PII from a docx file.

- **Request Parameters**: Multipart/form-data with the docx file.
- **Response**: JSON object with detected PII tags.

#### POST /docx/redact

Redacts PII from a docx file.

- **Request Body**: Multipart/form-data with a docx file and a form field for `pii_to_redact` (comma-separated list of PII types to redact).
- **Response**: Redacted image.

## Running the Application

### Start the Application

To start the application using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or using Gunicorn:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```
