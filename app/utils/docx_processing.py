from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from docx import Document
import re
import io
import json

# Load redaction patterns from the JSON file
with open('redaction_patterns.json', 'r') as file:
    redaction_patterns = json.load(file)

# Function to redact patterns based on common PII structures
def redact_common_patterns(text: str, patterns: dict, redact_state: dict) -> str:
    redacted_text = text
    
    # Check and redact address patterns
    if re.search(patterns['address_start_pattern'], text, re.IGNORECASE):
        redact_state['redact_address'] = True
        redacted_text = re.sub(patterns['address_start_pattern'], 'XXXX', redacted_text, flags=re.IGNORECASE)

    if redact_state['redact_address']:
        redacted_text = re.sub(r'.*', 'XXXX', redacted_text)  

    if re.search(patterns['address_end_pattern'], text):
        redact_state['redact_address'] = False
        redacted_text = re.sub(patterns['address_end_pattern'], 'XXXX', redacted_text)

    # Redact phone number pattern
    redacted_text = re.sub(patterns['phone_no_pattern'], 'XXXX', redacted_text)

    # Check and redact DOB patterns
    if re.search(patterns['dob_start_pattern'], text, re.IGNORECASE):
        redact_state['redact_dob'] = True
        redacted_text = re.sub(patterns['dob_start_pattern'], 'XXXX', redacted_text, flags=re.IGNORECASE)

    if redact_state['redact_dob']:
        redacted_text = re.sub(r'.*', 'XXXX', redacted_text) 

    if re.search(patterns['dob_end_pattern'], text):
        redact_state['redact_dob'] = False
        redacted_text = re.sub(patterns['dob_end_pattern'], 'XXXX', redacted_text)

    return redacted_text

# Function to redact specific PII patterns provided in the JSON configuration
def redact_specific_patterns(text: str, patterns: dict) -> str:
    redacted_text = text
    for pattern_name, pattern_value in patterns.items():
        redacted_text = re.sub(pattern_value, 'XXXX', redacted_text, flags=re.IGNORECASE)
    return redacted_text

# Function to redact PII in DOCX content based on both common and specific patterns
def redact_docx_content(doc: Document, document_type: str) -> tuple:
    common_patterns = redaction_patterns['common']
    redacted_texts = []
    redact_state = {
        'redact_address': False,
        'redact_dob': False
    }
    
    # Get specific patterns for the document type, if available
    specific_patterns = redaction_patterns.get(document_type, None)
    
    for para in doc.paragraphs:
        for run in para.runs:
            original_text = run.text.strip()
            if original_text:
                # Apply common redactions
                new_text = redact_common_patterns(original_text, common_patterns, redact_state)
                
                # Apply specific redactions, if defined
                if specific_patterns:
                    new_text = redact_specific_patterns(new_text, specific_patterns)
                
                # Replace text and log if any redaction was applied
                if original_text != new_text:
                    run.text = new_text
                    redacted_texts.append(original_text)
    
    return doc, redacted_texts

# Function to redact only specified PII types in text based on a list of PII items
def redact_specific_pii(text: str, pii_to_redact_list: list, document_type: str) -> str:
    common_patterns = redaction_patterns['common']
    pii_mapping = {
        'Address': ['address_start_pattern', 'address_end_pattern'],
        'Phone Number': ['phone_no_pattern'],
        'Date of Birth': ['dob_start_pattern', 'dob_end_pattern'],
        'Aadhaar Number': ['aadhar_pattern'],
        'PAN Number': ['pan_pattern'],
        'Driving License Number': ['license_pattern'],
        'VID Number': ['vid_pattern'],
        'Voter ID Number': ['voter_id_pattern']
    }
    patterns_to_redact = {}

    # Gather patterns based on selected PII types
    for pii in pii_to_redact_list:
        if pii in pii_mapping:
            for pattern_name in pii_mapping[pii]:
                patterns_to_redact[pattern_name] = common_patterns.get(pattern_name) or \
                                                   redaction_patterns.get(document_type, {}).get(pattern_name)

    return redact_specific_patterns(text, patterns_to_redact)

# Process and redact a DOCX file based on document type and specific PII items
def process_docx_file(doc: Document, document_type: str, pii_to_redact_list: list) -> tuple:
    redacted_texts = []
    for para in doc.paragraphs:
        for run in para.runs:
            original_text = run.text.strip()
            if original_text:
                new_text = redact_specific_pii(original_text, pii_to_redact_list, document_type)
                if original_text != new_text:
                    run.text = new_text
                    redacted_texts.append(original_text)
    return doc, redacted_texts
