import base64
import requests
import os
import json
from PIL import Image

SYSTEM_PROMPT = """Act as an OCR assistant. Analyze the provided image and:
1. Recognize all visible text in the image as accurately as possible.
2. Maintain the original structure and formatting of the text.
3. If any words or phrases are unclear, indicate this with [unclear] in your transcription.
Provide only the transcription without any additional comments."""

def encode_image_to_base64(image_path):
    """Convert an image file to a base64 encoded string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        print("Encoded Base64 String (truncated):", encoded_string[:100])  # Print first 100 characters
        return encoded_string

def perform_ocr(image_path):
    """Perform OCR on the given image using Llama 3.2-Vision."""
    base64_image = encode_image_to_base64(image_path)
    response = requests.post(
        "http://localhost:11434/api/chat",  # Ensure this URL matches your Ollama service endpoint
        json={
            "model": "llama3.2-vision",
            "messages": [
                {
                    "role": "user",
                    "content": SYSTEM_PROMPT,
                    "images": [base64_image],
                },
            ],
        },
        stream=True  # Enable streaming response
    )

    if response.status_code == 200:
        transcription = ""
        try:
            # Process each line of the streaming response
            for line in response.iter_lines():
                if line:  # Skip empty lines
                    try:
                        json_line = line.decode('utf-8')  # Decode the line
                        data = json.loads(json_line)  # Use standard json module
                        message_content = data.get("message", {}).get("content", "")
                        transcription += message_content  # Append content to transcription
                    except Exception as e:
                        print("Error processing line:", e)
            return transcription  
        except Exception as e:
            print("Error reading streaming response:", e)
            return None
    else:
        print("Error:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    image_path = "OG CARNET.jpeg"  # Replace with your image path 
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' does not exist.")
        exit(1)
    result = perform_ocr(image_path)
    if result:
        print("OCR Recognition Result:")
        print(result)