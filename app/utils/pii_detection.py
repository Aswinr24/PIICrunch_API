import json
import re
import os
from typing import List

with open('pii_patterns.json') as f:
    pii_patterns = json.load(f)

def detect_pii(text: str) -> List[str]:
    detected_pii = []
    for category, details in pii_patterns.items():
        if details.get("regex"):
            for pattern in details["regex"]:
                if re.search(pattern, text):
                    detected_pii.append(category)
                    break
    return detected_pii
