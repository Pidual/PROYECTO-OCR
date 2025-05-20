import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from shared.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_QUEUE

import uuid
import json
import base64
import pika
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Create required directories
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
RESULT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'resultados')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# RabbitMQ connection
def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT
    ))

@app.route('/procesar-imagen', methods=['POST'])
def process_image():
    """
    Endpoint that receives an image, saves it, and queues it for OCR processing
    """
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Handle image (either as file or base64)
    if 'image' in request.files:
        # Handle multipart/form-data
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        filename = os.path.join(UPLOAD_FOLDER, f"carnet_{job_id}{os.path.splitext(file.filename)[1]}")
        file.save(filename)
    elif request.is_json and 'image_base64' in request.json:
        # Handle base64 encoded image
        try:
            image_data = base64.b64decode(request.json['image_base64'])
            filename = os.path.join(UPLOAD_FOLDER, f"carnet_{job_id}.png")
            with open(filename, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            return jsonify({"error": f"Invalid base64 image: {str(e)}"}), 400
    else:
        return jsonify({"error": "No image provided"}), 400
    
    # Publish message to RabbitMQ
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='ocr_queue', durable=True)
        
        # Create message payload
        message = {
            "job_id": job_id,
            "filename": filename
        }
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key='ocr_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        
        connection.close()
        
        return jsonify({
            "job_id": job_id,
            "status": "enviado"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to queue job: {str(e)}"}), 500

@app.route('/resultado/<job_id>', methods=['GET'])
def get_result(job_id):
    """
    Endpoint to check the status of a processing job or retrieve results
    """
    # Validate job_id format (basic security check)
    try:
        uuid.UUID(job_id, version=4)
    except ValueError:
        return jsonify({"error": "Invalid job ID format"}), 400
    
    # Check if result file exists
    result_file = os.path.join(RESULT_FOLDER, f"{job_id}.json")
    
    if os.path.exists(result_file):
        try:
            with open(result_file, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"error": f"Failed to read result file: {str(e)}"}), 500
    else:
        return jsonify({
            "status": "procesando"
        })

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)