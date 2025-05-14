import os
import uuid
import json
import base64
import pika
import sys

# Add the src directory to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Update paths for the new directory structure
UPLOAD_FOLDER = 'data/uploads'
RESULT_FOLDER = 'data/resultados'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# RabbitMQ connection
def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters('localhost'))

@app.route('/procesar-imagen', methods=['POST'])
def process_image():
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Handle image (either as file or base64)
    if 'image' in request.files:
        # Handle multipart/form-data
        file = request.files['image']
        extension = os.path.splitext(file.filename)[1] if file.filename else '.png'
        filename = f"{UPLOAD_FOLDER}/{job_id}{extension}"
        file.save(filename)
    elif 'image_base64' in request.json:
        # Handle base64 encoded image
        image_data = base64.b64decode(request.json['image_base64'])
        filename = f"{UPLOAD_FOLDER}/{job_id}.png"
        with open(filename, 'wb') as f:
            f.write(image_data)
    else:
        return jsonify({"error": "No image provided"}), 400
    
    # Publish message to RabbitMQ
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue='ocr_queue', durable=True)
        
        message = {
            "job_id": job_id,
            "filename": filename
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='ocr_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        
        connection.close()
        
        return jsonify({
            "job_id": job_id,
            "status": "enviado"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/resultado/<job_id>', methods=['GET'])
def get_result(job_id):
    result_file = f"{RESULT_FOLDER}/{job_id}.json"
    
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({
            "status": "procesando"
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)