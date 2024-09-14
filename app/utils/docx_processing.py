from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from docx import Document
import re
import io
import json

with open('redaction_patterns.json', 'r') as file:
    redaction_patterns = json.load(file)

def redact_common_patterns(text, patterns, redact_state):
    redacted_text = text 
    if re.search(patterns['address_start_pattern'], text, re.IGNORECASE):
        redact_state['redact_address'] = True
        redacted_text = re.sub(patterns['address_start_pattern'], 'XXXX', redacted_text, flags=re.IGNORECASE)

    if redact_state['redact_address']:
        redacted_text = re.sub(r'.*', 'XXXX', redacted_text)  
        
    if re.search(patterns['address_end_pattern'], text):
        redact_state['redact_address'] = False
        redacted_text = re.sub(patterns['address_end_pattern'], 'XXXX', redacted_text)

    redacted_text = re.sub(patterns['phone_no_pattern'], 'XXXX', redacted_text)

    if re.search(patterns['dob_start_pattern'], text, re.IGNORECASE):
        redact_state['redact_dob'] = True
        redacted_text = re.sub(patterns['dob_start_pattern'], 'XXXX', redacted_text, flags=re.IGNORECASE)

    if redact_state['redact_dob']:
        redacted_text = re.sub(r'.*', 'XXXX', redacted_text) 

    if re.search(patterns['dob_end_pattern'], text):
        redact_state['redact_dob'] = False
        redacted_text = re.sub(patterns['dob_end_pattern'], 'XXXX', redacted_text)

    return redacted_text

def redact_specific_patterns(text, patterns):
    redacted_text = text
    for pattern_name, pattern_value in patterns.items():
        redacted_text = re.sub(pattern_value, 'XXXX', redacted_text, flags=re.IGNORECASE)
    
    return redacted_text

def redact_docx_content(doc, document_type):
    common_patterns = redaction_patterns['common']
    redacted_texts = []
    redact_state = {
        'redact_address': False,
        'redact_dob': False
    }
    if document_type in redaction_patterns and document_type != "unidentified":
        specific_patterns = redaction_patterns[document_type]
    else:
        specific_patterns = None
    for para in doc.paragraphs:
        for run in para.runs:
            original_text = run.text
            
            if original_text.strip(): 
                new_text = redact_common_patterns(original_text, common_patterns, redact_state)
                if specific_patterns:
                    new_text = redact_specific_patterns(new_text, specific_patterns)
                run.text = new_text
                if original_text != new_text:
                    redacted_texts.append(original_text)
    
    return doc, redacted_texts

def redact_specific_pii(text, pii_to_redact_list, document_type):
    
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
    
    for pii in pii_to_redact_list:
        if pii in pii_mapping:
            for pattern_name in pii_mapping[pii]:
                if pattern_name in common_patterns:
                    patterns_to_redact[pattern_name] = common_patterns[pattern_name]
                else:
                    if pattern_name in redaction_patterns.get(document_type, {}):
                        patterns_to_redact[pattern_name] = redaction_patterns[document_type][pattern_name]
    return redact_specific_patterns(text, patterns_to_redact)

def process_docx_file(doc: Document, document_type: str, pii_to_redact_list: list):
    redacted_texts = []
    for para in doc.paragraphs:
        for run in para.runs:
            original_text = run.text
            if original_text.strip():
                new_text = redact_specific_pii(original_text, pii_to_redact_list, document_type)
                run.text = new_text
                if original_text != new_text:
                    redacted_texts.append(original_text)
    return doc, redacted_texts
