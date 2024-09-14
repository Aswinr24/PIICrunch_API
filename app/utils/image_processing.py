import re
import cv2
import json

with open('redaction_patterns.json', 'r') as file:
    redaction_patterns = json.load(file)

def mask_text(image, bbox): 
    top_left = tuple([int(val) for val in bbox[0]])
    bottom_right = tuple([int(val) for val in bbox[2]])
    cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), thickness=-1)

def redact_common_patterns(image, results, patterns):
    redacted_texts = []
    start_redact = False
    start_redact2 = False
    
    for bbox, text, _ in results:
        if 'address_start_pattern' in patterns and re.search(patterns['address_start_pattern'], text, re.IGNORECASE):
            print(f"Redaction Start: {text}")
            start_redact = True
            redacted_texts.append(text)
            mask_text(image, bbox)
        elif start_redact and re.search(patterns['address_end_pattern'], text):
            print(f"Redacted Address End: {text}")
            redacted_texts.append(text)
            mask_text(image, bbox)
            start_redact = False
        elif start_redact:
            print(f"Redacting: {text}")
            redacted_texts.append(text)
            mask_text(image, bbox)

        if 'phone_no_pattern' in patterns and re.search(patterns['phone_no_pattern'], text):
            print(f"Redacting Phone Number: {text}")
            redacted_texts.append(text)
            mask_text(image, bbox)

        if 'dob_start_pattern' in patterns and re.search(patterns['dob_start_pattern'], text, re.IGNORECASE):
            print(f"Redaction Start: {text}")
            start_redact2 = True
            redacted_texts.append(text)
            mask_text(image, bbox)
        if start_redact2 and re.search(patterns['dob_end_pattern'], text):
            print(f"Redacting DOB: {text}")
            redacted_texts.append(text)
            mask_text(image, bbox)
            start_redact2 = False
        elif start_redact2:
            print(f"Redacting: {text}")
            redacted_texts.append(text)
            mask_text(image, bbox)

    return image, redacted_texts

def redact_specific_patterns(image, results, patterns):
    redacted_texts = []
    
    for bbox, text, _ in results:
        for pattern_name, pattern_value in patterns.items():
            if re.search(pattern_value, text, re.IGNORECASE):
                print(f"Redacting {pattern_name}: {text}")
                redacted_texts.append(text)
                mask_text(image, bbox)
    
    return image, redacted_texts

def redact(image, results, doc_type):
    redacted_texts = []
    
    common_patterns = redaction_patterns['common']
    image, common_redacted_texts = redact_common_patterns(image, results, common_patterns)
    redacted_texts.extend(common_redacted_texts)

    if doc_type in redaction_patterns and doc_type != "unidentified":
        specific_patterns = redaction_patterns[doc_type]
        image, specific_redacted_texts = redact_specific_patterns(image, results, specific_patterns)
        redacted_texts.extend(specific_redacted_texts)

    print("\nRedacted Texts:")
    for redacted in redacted_texts:
        print(redacted)

    return image

def redact_specific_pii(image, results, doc_type, pii_to_redact_list):
    redacted_texts = []

    common_patterns = redaction_patterns['common']
    specific_patterns = redaction_patterns.get(doc_type, {})
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
    for pii_to_redact in pii_to_redact_list:
        if pii_to_redact in pii_mapping:
            patterns_to_use = {}
            for pattern_name in pii_mapping[pii_to_redact]:
                if pattern_name in common_patterns:
                    patterns_to_use[pattern_name] = common_patterns[pattern_name]
                if pattern_name in specific_patterns:
                    patterns_to_use[pattern_name] = specific_patterns[pattern_name]
            if patterns_to_use:
                image, redacted_texts_partial = redact_common_patterns(image, results, patterns_to_use)
                image, redacted_texts_partial = redact_specific_patterns(image, results, patterns_to_use)
                redacted_texts.extend(redacted_texts_partial)
    print("\nRedacted Texts:")
    for redacted in redacted_texts:
        print(redacted)

    return image
