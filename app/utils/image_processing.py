from PIL import Image, ImageDraw, ImageFilter
import pytesseract
import json
import re
from typing import List, Tuple

with open('pii_patterns.json') as f:
    pii_patterns = json.load(f)

def preprocess_image(image: Image.Image) -> Image.Image:
    gray_image = image.convert('L')
    upscale_size = (gray_image.width * 2, gray_image.height * 2)
    upscaled_image = gray_image.resize(upscale_size, Image.LANCZOS)
    sharpened_image = upscaled_image.filter(ImageFilter.SHARPEN)
    
    return sharpened_image

# def get_pii_regions_textract(image_path: str) -> List[tuple]:
#     # Read image file
#     with open(image_path, 'rb') as image_file:
#         image_bytes = image_file.read()
#     response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
#     detected_pii_regions = []
    
#     # Open the image to get its dimensions
#     with Image.open(image_path) as image:
#         width, height = image.size

#         for item in response['Blocks']:
#             if item['BlockType'] == 'LINE':
#                 text = item['Text']
#                 bounding_box = item['Geometry']['BoundingBox']

#                 # Convert normalized bounding box to absolute coordinates
#                 left = int(bounding_box['Left'] * width)
#                 top = int(bounding_box['Top'] * height)
#                 right = int((bounding_box['Left'] + bounding_box['Width']) * width)
#                 bottom = int((bounding_box['Top'] + bounding_box['Height']) * height)

#                 # Check if the text matches any PII pattern
#                 for category, details in pii_patterns.items():
#                     if details.get("regex"):
#                         for pattern in details["regex"]:
#                             if re.search(pattern, text):
#                                 print(f"Detected PII: {text} in {category}")

#                                 detected_pii_regions.append((left, top, right, bottom))
    
#     return detected_pii_regions


# def mask_or_blur_image2(image: Image.Image, regions: List[tuple], action: str) -> Image.Image:
#     if image.mode != 'RGB':
#         image = image.convert('RGB')
#     draw = ImageDraw.Draw(image)
    
#     for region in regions:
#         left, top, right, bottom = region

#         # Ensure the coordinates are valid
#         if left < 0 or top < 0 or right <= left or bottom <= top:
#             print(f"Skipping invalid region: {region}")
#             continue

#         # Ensure coordinates are within image bounds
#         width, height = image.size
#         left = max(0, left)
#         top = max(0, top)
#         right = min(width, right)
#         bottom = min(height, bottom)

#         if action == "blur":
#             region_image = image.crop((left, top, right, bottom))
#             blurred_region = region_image.filter(ImageFilter.GaussianBlur(10))
#             image.paste(blurred_region, (left, top))
#         elif action == "mask":
#             draw.rectangle([left, top, right, bottom], fill="black")

#     return image

def get_pii_regions(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    detected_pii_regions = []
    text_positions = []

    for i, word in enumerate(ocr_data['text']):
        if word.strip() == '':
            continue
        x = ocr_data['left'][i]
        y = ocr_data['top'][i]
        w = ocr_data['width'][i]
        h = ocr_data['height'][i]
        left = x
        top = y
        right = x + w
        bottom = y + h
        
        text_positions.append({
            "word": word,
            "position": (left, top, right, bottom)
        })

    full_text = ' '.join([tp['word'] for tp in text_positions])
    for category, details in pii_patterns.items():
        if details.get("regex"):
            for pattern in details["regex"]:
                match = re.search(pattern, full_text)
                if match:
                    matched_text = match.group()
                    print(f"Detected PII: {matched_text}")
                    matched_words = matched_text.split()
                    for tp in text_positions:
                        if any(mw in tp['word'] for mw in matched_words):
                            detected_pii_regions.append(tp['position'])
    
    return detected_pii_regions
def mask_or_blur_image(image: Image.Image, regions: List[Tuple[int, int, int, int]], action: str) -> Image.Image:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    draw = ImageDraw.Draw(image)
    
    for region in regions:
        left, top, right, bottom = region
        if left < 0 or top < 0 or right <= left or bottom <= top:
            print(f"Skipping invalid region: {region}")
            continue
        width, height = image.size
        left = max(0, left)
        top = max(0, top)
        right = min(width, right)
        bottom = min(height, bottom)

        if action == "blur":
            region_image = image.crop((left, top, right, bottom))
            blurred_region = region_image.filter(ImageFilter.GaussianBlur(10))
            image.paste(blurred_region, (left, top))
        elif action == "mask":
            draw.rectangle([left, top, right, bottom], fill="black")

    return image