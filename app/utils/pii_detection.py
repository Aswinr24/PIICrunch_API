import json
import re
from typing import List, Tuple, Dict

# Load patterns and keywords with error handling
try:
    with open('pii_patterns.json') as f:
        pii_patterns: Dict[str, Dict[str, List[str]]] = json.load(f)
    with open('keywords.json') as f:
        document_keywords: Dict[str, List[str]] = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise RuntimeError("Error loading JSON configuration files") from e

def detect_pii(text: str) -> Tuple[List[str], str]:
    detected_pii = []
    document_type = "Govt document type unidentified"
    
    # Identify document type based on keywords
    for doc_type, keywords in document_keywords.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            document_type = doc_type
            break

    # Detect PII categories using regex patterns
    for category, details in pii_patterns.items():
        patterns = details.get("regex", [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected_pii.append(category)
                break  # Stop after first match for efficiency in each category
    
    return detected_pii, document_type
