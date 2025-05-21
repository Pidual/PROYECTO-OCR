import sys
import os
import uuid
import json
import base64
import sqlite3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import pika

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from shared.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_QUEUE
from database import init_db, DB_PATH 
# Load environment variables
load_dotenv()

# Initialize database
init_db() 

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
    job_id = str(uuid.uuid4())
    
    # Handle image (either as file or base64)
    if 'image' in request.files:
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        filename = os.path.join(UPLOAD_FOLDER, f"carnet_{job_id}{os.path.splitext(file.filename)[1]}")
        file.save(filename)
    elif request.is_json and 'image_base64' in request.json:
        try:
            image_data = base64.b64decode(request.json['image_base64'])
            filename = os.path.join(UPLOAD_FOLDER, f"carnet_{job_id}.png")
            with open(filename, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            return jsonify({"error": f"Invalid base64 image: {str(e)}"}), 400
    else:
        return jsonify({"error": "No image provided"}), 400
    
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        message = {
            "job_id": job_id,
            "filename": filename
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
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
    try:
        uuid.UUID(job_id, version=4)
    except ValueError:
        return jsonify({"error": "Invalid job ID format"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM resultados WHERE job_id = ?", (job_id,))
        row = c.fetchone()
        conn.close()

        if row:
            result = {
                "job_id": row[0],
                "nombre": row[1],
                "codigo_estudiante": row[2],
                "carrera": row[3],
                "institucion": row[4],
                "status": row[5],
                "processed_at": row[6],
                "raw_text": row[7],
                "confidence": {
                    "nombre": row[8],
                    "codigo_estudiante": row[9],
                    "carrera": row[10]
                }
            }
            return jsonify(result)
        else:
            return jsonify({"status": "procesando"})
    except Exception as e:
        return jsonify({"error": f"Failed to read result from database: {str(e)}"}), 500

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
