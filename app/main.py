from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import image_routes, pdf_routes, docx_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_routes.router, prefix="/image", tags=["image"])
app.include_router(pdf_routes.router, prefix="/pdf", tags=["pdf"])
app.include_router(docx_routes.router, prefix="/docx", tags=["docx"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the PII Crunch API!"}