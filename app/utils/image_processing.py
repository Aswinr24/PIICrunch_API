import re
import cv2
import json

# Load redaction patterns with error handling
try:
    with open('redaction_patterns.json', 'r') as file:
        redaction_patterns = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    raise RuntimeError("Error loading redaction patterns") from e

# Function to mask text in the image based on bounding box (bbox)
def mask_text(image, bbox): 
    top_left = tuple(map(int, bbox[0]))
    bottom_right = tuple(map(int, bbox[2]))
    cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), thickness=-1)

# Function to redact common patterns such as address and phone numbers
def redact_common_patterns(image, results, patterns):
    redacted_texts = []
    start_redact = False

    for i, (bbox, text, _) in enumerate(results):
        # Address Redaction
        if 'address_start_pattern' in patterns and re.search(patterns['address_start_pattern'], text, re.IGNORECASE):
            start_redact = True
            redacted_texts.append(text)
            mask_text(image, bbox)
        elif start_redact and re.search(patterns['address_end_pattern'], text):
            redacted_texts.append(text)
            mask_text(image, bbox)
            start_redact = False
        elif start_redact:
            redacted_texts.append(text)
            mask_text(image, bbox)
        
        # Phone Number Redaction
        if 'phone_no_pattern' in patterns and re.search(patterns['phone_no_pattern'], text):
            redacted_texts.append(text)
            mask_text(image, bbox)
        
        # Date of Birth Redaction
        if 'dob_pattern' in patterns and re.search(patterns['dob_pattern'], text, re.IGNORECASE):
            redacted_texts.append(text)
            mask_text(image, bbox)
        
        # Name Redaction
        if 'name_pattern' in patterns and re.search(patterns['name_pattern'], text, re.IGNORECASE):
            next_bbox, next_text, _ = results[i + 1] if i + 1 < len(results) else (None, None, None)
            if next_bbox:
                redacted_texts.append(next_text)
                mask_text(image, next_bbox)
                
        # Father's Name Redaction
        if 'fathers_name_pattern' in patterns and re.search(patterns['fathers_name_pattern'], text, re.IGNORECASE):
            next_bbox, next_text, _ = results[i + 1] if i + 1 < len(results) else (None, None, None)
            if next_bbox:
                redacted_texts.append(next_text)
                mask_text(image, next_bbox)
            
    return image, redacted_texts

# Function to redact specific patterns like Aadhaar, PAN based on patterns
def redact_specific_patterns(image, results, patterns):
    redacted_texts = []

    for bbox, text, _ in results:
        for pattern_name, pattern_value in patterns.items():
            if re.search(pattern_value, text, re.IGNORECASE):
                redacted_texts.append(text)
                mask_text(image, bbox)
    
    return image, redacted_texts

# Main function to apply redactions based on document type
def redact(image, results, doc_type):
    redacted_texts = []
    common_patterns = redaction_patterns.get('common', {})
    
    # Apply common pattern redactions
    image, common_redacted_texts = redact_common_patterns(image, results, common_patterns)
    redacted_texts.extend(common_redacted_texts)

    # Apply specific pattern redactions if available
    specific_patterns = redaction_patterns.get(doc_type, {})
    image, specific_redacted_texts = redact_specific_patterns(image, results, specific_patterns)
    redacted_texts.extend(specific_redacted_texts)

    print("\nRedacted Texts:")
    for redacted in redacted_texts:
        print(redacted)

    return image

# Function to redact only selected PII categories
def redact_specific_pii(image, results, doc_type, pii_to_redact_list):
    redacted_texts = []
    common_patterns = redaction_patterns.get('common', {})
    specific_patterns = redaction_patterns.get(doc_type, {})
    
    pii_mapping = {
        'Address': ['address_start_pattern', 'address_end_pattern'],
        'Phone Number': ['phone_no_pattern'],
        'Date of Birth': ['dob_pattern'],
        'Name': ['name_pattern'],
        'Father\'s Name': ['fathers_name_pattern'],
        'Aadhaar Number': ['aadhar_pattern'],
        'PAN Number': ['pan_pattern'],
        'Driving License Number': ['license_pattern'],
        'VID Number': ['vid_pattern'],
        'Voter ID Number': ['voter_id_pattern']
    }

    # Collect patterns for specified PII categories
    patterns_to_use = {}
    for pii in pii_to_redact_list:
        for pattern_name in pii_mapping.get(pii, []):
            pattern = common_patterns.get(pattern_name) or specific_patterns.get(pattern_name)
            if pattern:
                patterns_to_use[pattern_name] = pattern

    # Apply redactions
    if patterns_to_use:
        image, partial_redacted_texts = redact_common_patterns(image, results, patterns_to_use)
        image, partial_redacted_texts = redact_specific_patterns(image, results, patterns_to_use)
        redacted_texts.extend(partial_redacted_texts)

    print("\nRedacted Texts:")
    for redacted in redacted_texts:
        print(redacted)

    return image
