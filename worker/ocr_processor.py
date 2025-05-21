import base64
import requests
import json
import time
from PIL import Image
import io
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
OLLAMA_MODEL = "qwen2.5vl:7b"  # Hardcoded model name

def process_image_ocr(image_path, max_retries=3):
    """
    Process an image using the Ollama OCR model with retry logic
    No image modifications applied - using original image
    """
    # Process with multiple retry attempts
    for attempt in range(max_retries):
        try:
            print(f"OCR processing attempt {attempt+1}/{max_retries}")
            
            # Encode original image to base64 without any modifications
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Use a specific prompt for OCR
            system_prompt = """This is an OCR task. TRANSCRIBE ALL TEXT from this student ID card image.

DO NOT describe the image. DO NOT count fields.
DO NOT say what's visible or not visible.
ONLY TRANSCRIBE THE ACTUAL TEXT you can see on the card.

Look for and transcribe:
- Student name
- Student ID number/code
- Program/major
- University name

Format each field with a label EXACTLY like this:
Nombre: [transcribed student name]
Código: [transcribed student ID number]
Carrera: [transcribed program/major]
Institución: [transcribed university name]"""
            
            # Non-streaming approach
            import json
            import os

            # Get parameters from environment
            params_str = os.getenv('OLLAMA_PARAMETERS', '{}')
            model_params = json.loads(params_str)

            # Add to your API request
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": system_prompt,
                            "images": [base64_image],
                        },
                    ],
                    "stream": False,
                    **model_params,  # Add all parameters from config
                },
                timeout=180,  # Increased timeout from 90 to 180 seconds
            )
            
            if response.status_code == 200:
                data = response.json()
                ocr_text = data.get("message", {}).get("content", "")
                if ocr_text:
                    print("OCR processing successful")
                    return ocr_text
                else:
                    print("OCR returned empty response")
            else:
                print(f"Error from Ollama API: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error in OCR processing: {e}")
        
        # Wait before retrying
        if attempt < max_retries - 1:
            sleep_time = 5 * (attempt + 1)
            print(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
    
    return None

def extract_fields(text):
    """Improved extraction with better institution handling"""
    extracted_data = {
        "raw_text": text,
        "nombre": "",
        "codigo_estudiante": "",
        "carrera": "",
        "institucion": ""
    }
    
    # Parse labeled output (if model followed the prompt format)
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line.lower().startswith("nombre:"):
            extracted_data["nombre"] = line[7:].strip()
        elif line.lower().startswith("código:") or line.lower().startswith("codigo:"):
            extracted_data["codigo_estudiante"] = line[7:].strip()
        elif line.lower().startswith("carrera:"):
            extracted_data["carrera"] = line[8:].strip()
        elif line.lower().startswith("institución:") or line.lower().startswith("institucion:"):
            extracted_data["institucion"] = line[12:].strip()
    
    # Extract institution if not found above
    if not extracted_data["institucion"]:
        # Look for university names
        import re
        uni_patterns = [
            r"(?i)universidad\s+([^\s,.]+(?:\s+[^\s,.]+){0,3})",
            r"(?i)([^\s,.]+)\s+university",
            r"(?i)(UPTC)"
        ]
        
        for pattern in uni_patterns:
            matches = re.search(pattern, text)
            if matches:
                extracted_data["institucion"] = matches.group(0).strip()
                break
    
    # More extraction logic as fallback...
    # (keep your existing extraction code here)
    
    return extracted_data