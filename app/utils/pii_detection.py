import json
import re
from typing import List, Tuple

with open('pii_patterns.json') as f:
    pii_patterns = json.load(f)
    
with open('keywords.json') as f:
    document_keywords = json.load(f)

def detect_pii(text: str) -> Tuple[List[str], str]:
    detected_pii = []
    document_type = "Govt document type unidentified"  

    for doc_type, keywords in document_keywords.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            document_type = doc_type
            break

    for category, details in pii_patterns.items():
        if details.get("regex"):
            for pattern in details["regex"]:
                if re.search(pattern, text):
                    
                    detected_pii.append(category)
                    
    return detected_pii, document_type

def detect_docType(text: str) -> str:
    document_type = "unidentified"  
    for doc_type, keywords in document_keywords.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            document_type = doc_type
            break
    return document_type